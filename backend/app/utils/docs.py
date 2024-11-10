import os
import re
import pickle
from typing import List, Dict, Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import asyncio
import json
from typing import Dict, Any
from openai import AsyncOpenAI

client = AsyncOpenAI()

def create_services():
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents'
    ]
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv('CREDENTIALS_FILE'),
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

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
                fields="nextPageToken, files(id, name)",
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

async def process_feedback(document: Dict[str, Any], drive_service, file_id: str):
    """Process document feedback request and create multiple targeted comments."""

    # Load feedback prompt
    with open(os.getenv("FEEDBACK_PROMPT_FILE"), 'r') as f:
        prompt = json.loads(f.read())
        for message in prompt:
            message["content"] = message["content"].format(
                document=format_document(document)
            )

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
    try:
        document = read_document_content(docs_service, file_id)

        # Check if this is a feedback request
        if "#feedback" in get_latest_comment_reply(comment)["content"].lower():
            await process_feedback(document, drive_service, file_id)
            reply_to_comment(
                drive_service,
                file_id,
                comment.get("id"),
                "I've reviewed the document and left detailed feedback as comments throughout. Let me know if you'd like me to clarify any points."
            )
            return

        # Standard comment processing
        selection = get_selected_text(document, comment)

        with open(os.getenv("PROMPT_FILE"), 'r') as f:
            prompt = json.loads(f.read())
            for message in prompt:
                message["content"] = message["content"].format(
                    AGENT_ID=os.getenv('AGENT_ID'),
                    document=format_document(document),
                    comment=format_comment(comment),
                    selection=selection
                )

        response = await client.chat.completions.create(
            model=os.getenv('MODEL_NAME'),
            messages=prompt,
            temperature=0.7
        )
        reply = response.choices[0].message.content

        reply_to_comment(drive_service, file_id, comment.get("id"), reply)
    except Exception as e:
        print(f"Error while processing comment: {e}")
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
