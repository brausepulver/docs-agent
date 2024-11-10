import os
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
        document = docs_service.documents().get(documentId=document_id).execute()
        return document
    except Exception as e:
        print(f"Error reading document: {e}")
        raise

def add_comment(drive_service, file_id: str, content: str) -> Dict[str, Any]:
    try:
        result = drive_service.comments().create(
            fileId=file_id,
            body={'content': content},
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
                fields='comments(id,content,modifiedTime,author,replies,resolved,deleted),nextPageToken',
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
        response = drive_service.changes().list(pageToken=page_token, spaces="drive", restrictToMyDrive=False, includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
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

async def process_comment(file_id: str, comment: Dict[str, Any], processing: set, drive_service, docs_service, stop_event):
    try:
        document = read_document_content(docs_service, file_id)

        with open(os.getenv("PROMPT_FILE"), 'r') as f:
            prompt = json.loads(f.read())
            for message in prompt:
                message["content"] = message["content"].format(AGENT_ID=os.getenv('AGENT_ID'), document=format_document(document), comment=format_comment(comment))

        response = await client.chat.completions.create(model=os.getenv('MODEL_NAME'), messages=prompt, temperature=0.7)
        reply = response.choices[0].message.content

        reply_to_comment(drive_service, file_id, comment.get("id"), reply)
    except Exception as e:
        print(f"Error while processing comment: {e}")
    finally:
        processing.remove(comment.get("id"))

def should_process_comment(comment):
    if comment.get("deleted") or comment.get("resolved") or comment.get("author", {}).get("me"): return False

    replies = list(filter(lambda reply: not reply.get("deleted"), comment.get("replies", [])))
    def did_reply(replies):
        return any(map(lambda reply: reply.get("author", {}).get("me"), replies))

    if os.getenv('AGENT_ID') in comment.get("content") and not did_reply(replies): return True

    for i, reply in enumerate(replies):
        if os.getenv('AGENT_ID') in reply.get("content") and not did_reply(replies[i+1:]): return True

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
            if file.get("viewedByMeTime") or (file_id in accessed): continue
            accessed.add(file_id)

            comments = list_comments_for_file(drive_service, file_id)
            comments.extend(map(lambda comment: (file_id, comment), comments))

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
            file_comments.extend(map(lambda comment: (file_id, comment), list_comments_for_file(drive_service, file_id)))

        file_comments = list(filter(lambda pair: should_process_comment(pair[1]), file_comments))
        for file_id, comment in file_comments:
            if comment.get("id") in processing: continue

            processing.add(comment.get("id"))
            asyncio.create_task(process_comment(file_id, comment, processing, drive_service, docs_service, stop_event))

    return process_comments
