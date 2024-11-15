import os
import re
from typing import List, Dict, Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import asyncio
import json
from typing import Dict, Any
from openai import AsyncOpenAI
from llama_index.core import Document as LlamaDocument, VectorStoreIndex
from llama_index.readers.google import GoogleDocsReader
from .db import AsyncSessionLocal
from sqlalchemy import select, text
from .llamaindex import gdrive_vector_store, gdrive_storage_context, get_relevant_chunks

client = AsyncOpenAI()

def create_services():
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents'
    ]
    creds = None

    if os.path.exists('token.json'):
        with open('token.json', 'r') as token:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv('CREDENTIALS_FILE'),
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    drive_service = build('drive', 'v3', credentials=creds)
    docs_service = build('docs', 'v1', credentials=creds)

    return drive_service, docs_service

def read_document_content(docs_service, document_id: str) -> Dict[str, Any]:
    try:
        document = docs_service.documents().get(
            documentId=document_id,
            fields='body,documentId,documentStyle,namedStyles,revisionId,suggestionsViewMode'
        ).execute()
        return document
    except Exception as e:
        print(f"Error reading document: {e}")
        raise

def get_selected_text(document: Dict[str, Any], comment: Dict[str, Any]) -> str:
    if 'quotedFileContent' not in comment:
        return ""

    quoted_content = comment['quotedFileContent'] if 'quotedFileContent' in comment else {}
    if not quoted_content:
        return ""

    quoted = quoted_content.get('value', {})
    return quoted if quoted else ""

def add_comment(drive_service, file_id: str, content: str, quoted_text: str = None) -> Dict[str, Any]:
    """Create an unanchored comment on a Google Doc with quoted content."""
    try:
        body = { 'content': content }

        if quoted_text:
            body['quotedFileContent'] = { 'value': quoted_text, 'mimeType': 'text/plain' }

        result = drive_service.comments().create(
            fileId=file_id,
            body=body,
            fields='id,content,modifiedTime,author'
        ).execute()
        return result
    except Exception as e:
        print(f"Error adding comment: {e}")
        raise

def reply_to_comment(drive_service, file_id: str, comment_id: str, content: str) -> Dict[str, Any]:
    try:
        result = drive_service.replies().create(
            fileId=file_id,
            commentId=comment_id,
            body={'content': content},
            fields='id,content,modifiedTime,author'
        ).execute()
        return result
    except Exception as e:
        print(f"Error replying to comment: {e}")
        raise

def list_comments_for_file(drive_service, file_id: str, include_resolved: bool = False) -> List[Dict[str, Any]]:
    try:
        comments = []
        page_token = None

        while True:
            response = drive_service.comments().list(
                fileId=file_id,
                pageSize=100,
                pageToken=page_token,
                fields='comments(id,content,modifiedTime,author,replies,resolved,deleted,quotedFileContent)',
                includeDeleted=False
            ).execute()

            current_comments = response.get('comments', [])

            if not include_resolved:
                current_comments = [
                    comment for comment in current_comments
                    if not comment.get('resolved', False)
                ]

            comments.extend(current_comments)

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return comments
    except Exception as e:
        print(f"Error listing comments: {e}")
        raise

def list_files(drive_service) -> List[Dict[str, str]]:
    docs = []
    page_token = None

    while True:
        try:
            results = drive_service.files().list(
                q="mimeType='application/vnd.google-apps.document'",
                pageSize=1000,
                fields="nextPageToken, files(id, name, ownedByMe, owners)",  # Added ownedByMe and owners
                pageToken=page_token,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()

            docs.extend(results.get('files', []))
            page_token = results.get('nextPageToken')

            if not page_token:
                break
        except Exception as e:
            print(f"Error fetching docs: {e}")
            break

    return docs

def get_start_page_token(drive_service):
    try:
        response = drive_service.changes().getStartPageToken().execute()
    except HttpError as error:
        print(f"Error fetching start page token: {error}")
        raise
    return response.get("startPageToken")

def list_changes(drive_service, page_token):
    changes = []

    try:
        while page_token is not None:
            response = drive_service.changes().list(
                pageToken=page_token,
                spaces="drive",
                restrictToMyDrive=False,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            changes.extend(response.get("changes", []))
            if "newStartPageToken" in response:
                page_token = response.get("newStartPageToken")
                break
            page_token = response.get("nextPageToken", response.get("newStartPageToken"))

    except HttpError as error:
        print(f"Error fetching changes: {error}")
        raise

    return changes, page_token

def format_comment(comment):
    thread = []
    for entity in [comment] + comment.get("replies", []):
        thread.append({
            "role": "user" if not entity.get("me", False) else "assistant",
            "timestamp": entity.get("modifiedTime"),
            "content": entity.get("content"),
            "author": entity.get("author", {}).get("displayName", "Unknown")
        })
    return json.dumps(thread, indent=2)

def format_document(document):
    def extract_text_from_structural_element(element):
        text = []
        if 'paragraph' in element:
            text.extend(extract_text_from_paragraph(element['paragraph']))
        elif 'table' in element:
            text.extend(extract_text_from_table(element['table']))
        elif 'tableOfContents' in element:
            pass
        return text

    def extract_text_from_paragraph(paragraph):
        text = []
        for element in paragraph.get('elements', []):
            if 'textRun' in element:
                text.append(element['textRun'].get('content', ''))
        return text

    def extract_text_from_table(table):
        text = []
        for row in table.get('tableRows', []):
            row_text = []
            for cell in row.get('tableCells', []):
                cell_text = []
                for content in cell.get('content', []):
                    cell_text.extend(extract_text_from_structural_element(content))
                row_text.append(''.join(cell_text))
            text.append(' | '.join(filter(None, row_text)))
        return text

    text_parts = []

    if 'body' in document:
        for content in document['body'].get('content', []):
            text_parts.extend(extract_text_from_structural_element(content))

    return '\n'.join(filter(None, text_parts))

def get_latest_comment_reply(comment):
    replies = comment.get("replies", [])
    if not replies:
        return comment
    return get_latest_comment_reply(replies[-1])

def format_chunks(chunks):
    return "\n\n".join([f"• {chunk.text}" for chunk in chunks])

async def process_feedback(document: Dict[str, Any], drive_service, file_id: str):
    """Process document feedback request and create multiple targeted comments."""

    content = format_document(document)
    chunks = await get_relevant_chunks(
        vector_store=gdrive_vector_store,
        query=content,
        num_chunks=5,
        not_doc_id=file_id
    )

    # Load feedback prompt
    with open(os.getenv("FEEDBACK_PROMPT_FILE"), 'r') as f:
        prompt = json.loads(f.read())
        for message in prompt:
            message["content"] = message["content"].format(document=content, context=format_chunks(chunks))

    # Get structured feedback from LLM
    response = await client.chat.completions.create(
        model=os.getenv('MODEL_NAME'),
        messages=prompt,
        temperature=0.7
    )

    feedback = response.choices[0].message.content
    comments = parse_feedback(feedback)

    # Create comments for each feedback item
    for comment in comments:
        try:
            add_comment(
                drive_service=drive_service,
                file_id=file_id,
                content=comment["content"],
                quoted_text=comment["quoted_text"]
            )
        except Exception as e:
            print(f"Error creating feedback comment: {e}")
            continue

def parse_feedback(feedback_text: str) -> List[Dict[str, str]]:
    """Parse the LLM's feedback response into structured comments.

    Expected format from LLM:
    ---
    [Section: "quoted text here"]
    Feedback content here
    ---
    [Section: "another quoted text"]
    More feedback here
    ---
    """
    comments = []
    sections = feedback_text.split('---\n')

    for section in sections:
        if not section.strip():
            continue

        try:
            # Extract the quoted section and feedback content
            section_match = re.match(r'\[Section: "(.*?)"\]\s*(.*)',
                                   section.strip(),
                                   re.DOTALL)

            if section_match:
                quoted_text = section_match.group(1)
                feedback_content = section_match.group(2).strip()

                comments.append({
                    "content": feedback_content,
                    "quoted_text": quoted_text
                })

        except Exception as e:
            print(f"Error parsing feedback section: {e}")
            continue

    return comments

async def process_comment(file_id: str, comment: Dict[str, Any], processing: set, drive_service, docs_service, stop_event):
    # Add a processing reply first
    processing_reply = reply_to_comment(
        drive_service,
        file_id,
        comment.get("id"),
        "Taking a look 👀"
    )

    try:
        document = read_document_content(docs_service, file_id)

        # Check if this is a feedback request
        if "#feedback" in get_latest_comment_reply(comment)["content"].lower():
            await process_feedback(document, drive_service, file_id)

            # Delete the processing reply and create a new one
            drive_service.replies().delete(
                fileId=file_id,
                commentId=comment.get("id"),
                replyId=processing_reply.get("id")
            ).execute()

            reply_to_comment(
                drive_service,
                file_id,
                comment.get("id"),
                "I've reviewed the document and left detailed feedback as comments throughout. Let me know if you'd like me to clarify any points. The comments are available in the right sidebar."
            )
            return

        # Standard comment processing
        selection = get_selected_text(document, comment)

        content = format_document(document)
        chunks = await get_relevant_chunks(
            vector_store=gdrive_vector_store,
            query=content,
            num_chunks=5,
            not_doc_id=file_id
        )
        context = format_chunks(chunks)

        with open(os.getenv("PROMPT_FILE"), 'r') as f:
            prompt = json.loads(f.read())
            for message in prompt:
                message["content"] = message["content"].format(
                    AGENT_ID=os.getenv('AGENT_ID'),
                    document=content,
                    comment=format_comment(comment),
                    selection=selection,
                    context=context
                )

        response = await client.chat.completions.create(
            model=os.getenv('MODEL_NAME'),
            messages=prompt,
            temperature=0.7
        )
        reply = response.choices[0].message.content

        # Delete the processing reply and create a new one
        drive_service.replies().delete(
            fileId=file_id,
            commentId=comment.get("id"),
            replyId=processing_reply.get("id")
        ).execute()

        reply_to_comment(
            drive_service,
            file_id,
            comment.get("id"),
            reply
        )

    except Exception as e:
        print(f"Error while processing comment: {e}")
        # Delete the processing reply and create error message
        try:
            drive_service.replies().delete(
                fileId=file_id,
                commentId=comment.get("id"),
                replyId=processing_reply.get("id")
            ).execute()

            reply_to_comment(
                drive_service,
                file_id,
                comment.get("id"),
                "I apologize, but I encountered an error while processing your request. Please try again."
            )
        except Exception as update_error:
            print(f"Error handling reply update: {update_error}")
    finally:
        processing.remove(comment.get("id"))

def should_process_comment(comment):
    if comment.get("deleted") or comment.get("resolved") or comment.get("author", {}).get("me"):
        return False

    replies = list(filter(lambda reply: not reply.get("deleted"), comment.get("replies", [])))
    def did_reply(replies):
        return any(map(lambda reply: reply.get("author", {}).get("me"), replies))

    # Check for feedback request
    if "#feedback" in get_latest_comment_reply(comment)["content"].lower():
        return True

    if os.getenv('AGENT_ID') in comment.get("content") and not did_reply(replies):
        return True

    for i, reply in enumerate(replies):
        if os.getenv('AGENT_ID') in reply.get("content") and not did_reply(replies[i+1:]):
            return True

    return False

def add_initial_greeting(drive_service, file_id: str) -> None:
    """Add a greeting comment when a document is first shared."""
    try:
        greeting = (
            f"Hi there! 👋 I'm {os.getenv('AGENT_ID')}, your AI writing assistant. "
            "I'm here to help with your document. You can:\n\n"
            "• Tag me in any comment by mentioning my name\n"
            "• Ask for comprehensive document feedback using #feedback\n"
            "• Quote specific text for targeted feedback\n\n"
            "Looking forward to helping you improve your document!"
        )

        add_comment(
            drive_service=drive_service,
            file_id=file_id,
            content=greeting
        )
    except Exception as e:
        print(f"Error adding greeting comment: {e}")
        raise

def has_agent_commented(drive_service, file_id: str) -> bool:
    """Check if the agent has already commented on this document."""
    try:
        comments = list_comments_for_file(drive_service, file_id, include_resolved=True)
        return any(
            comment.get("author", {}).get("me", False)
            or any(
                reply.get("author", {}).get("me", False)
                for reply in comment.get("replies", [])
            )
            for comment in comments
        )
    except Exception as e:
        print(f"Error checking for agent comments: {e}")
        return True  # Assume commented in case of error to prevent duplicate greetings

def get_initial_comments(drive_service, accessed):
    comments = []

    try:
        results = drive_service.files().list(
            q="sharedWithMe",
            fields="files(id, viewedByMeTime)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        for file in results.get("files", []):
            file_id = file.get("id")
            if file.get("viewedByMeTime") or (file_id in accessed):
                continue
            accessed.add(file_id)

            # Check if we need to add an initial greeting
            if not has_agent_commented(drive_service, file_id):
                add_initial_greeting(drive_service, file_id)

            file_comments = list_comments_for_file(drive_service, file_id)
            comments.extend(map(lambda comment: (file_id, comment), file_comments))

    except Exception as e:
        print(f"Error activating files: {e}")
        raise

    return comments

def create_process_comments():
    drive_service, docs_service = create_services()
    page_token = get_start_page_token(drive_service)
    processing = set()
    accessed = set()

    async def process_comments(stop_event):
        file_comments = get_initial_comments(drive_service, accessed)

        nonlocal page_token
        changes, page_token = list_changes(drive_service, page_token)

        for change in changes:
            if stop_event.is_set(): break
            file_id = change.get("fileId")
            if not file_id or change.get("removed"): continue

            # Handle newly shared documents
            if not has_agent_commented(drive_service, file_id) and file_id not in accessed:
                accessed.add(file_id)
                add_initial_greeting(drive_service, file_id)

            file_comments.extend(map(
                lambda comment: (file_id, comment),
                list_comments_for_file(drive_service, file_id)
            ))

        file_comments = list(filter(lambda pair: should_process_comment(pair[1]), file_comments))
        for file_id, comment in file_comments:
            if comment.get("id") in processing:
                continue

            processing.add(comment.get("id"))
            asyncio.create_task(
                process_comment(
                    file_id, comment, processing,
                    drive_service, docs_service, stop_event
                )
            )

    return process_comments

def create_process_gdrive():
    drive_service, _ = create_services()
    process_lock = asyncio.Lock()

    async def process_gdrive(stop_event):
        if process_lock.locked(): return

        async with process_lock, AsyncSessionLocal() as db:
            try:
                current_files = list_files(drive_service)
                current_file_ids = {doc['id'] for doc in current_files}

                existing_files = set()
                try:
                    query = select(text("DISTINCT metadata_->>'google_doc_id' as doc_id")).select_from(text('data_embeddings_google_drive'))
                    results = await db.execute(query)
                    existing_files = {row[0] for row in results if row[0]}
                except:
                    print(f"Error querying existing embeddings: {e}")
                    return

                files_to_process = [
                    doc for doc in current_files
                    if doc['id'] not in existing_files
                ]
                files_to_remove = existing_files - current_file_ids

                if files_to_remove:
                    try:
                        for file_id in files_to_remove:
                            delete_query = text("DELETE FROM data_embeddings_google_drive WHERE metadata_->>'google_doc_id' = :file_id")
                            await db.execute(delete_query, {"file_id": file_id})
                    except Exception as e:
                        print(f"Error removing embeddings: {e}")

                if files_to_process:
                    try:
                        reader = GoogleDocsReader()

                        doc_metadata = {
                            doc['id']: {
                                'google_doc_id': doc['id'],
                                'title': doc['name'],
                                'owner': doc['owners'][0]['emailAddress'] if doc.get('owners') else None
                            }
                            for doc in files_to_process
                        }

                        documents = reader.load_data(document_ids=[doc['id'] for doc in files_to_process])

                        llama_docs = [
                            LlamaDocument(
                                text=document.text,
                                metadata={**doc_metadata[document.metadata['document_id']], **document.metadata}
                            )
                            for document in documents
                        ]

                        VectorStoreIndex.from_documents(llama_docs, storage_context=gdrive_storage_context, show_progress=True)
                    except Exception as e:
                        print(f"Error processing documents: {e}")
            except Exception as e:
                print(f"Error processing Google Drive: {e}")

    return process_gdrive
