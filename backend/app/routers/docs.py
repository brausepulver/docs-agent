import os
from fastapi import Depends, HTTPException, APIRouter
from ..utils.auth import get_current_user
from ..utils.docs import create_services, list_files
from typing import List, Dict, Any

router = APIRouter()

@router.get("/api/documents", response_model=List[Dict[str, Any]])
async def get_documents_for_user(user_email: str = Depends(get_current_user)):
    drive_service, _ = create_services()
    try:
        # Fetch and filter documents based on user ownership
        all_docs = list_files(drive_service)
        user_docs = [
            doc for doc in all_docs
            if any(owner.get("emailAddress") == user_email for owner in doc.get("owners", []))
        ]
        return user_docs
    except Exception as e:
        print(f"Error fetching documents for user: {e}")
        raise HTTPException(status_code=500, detail="Error fetching documents")

@router.delete("/api/documents/{doc_id}")
async def remove_document(doc_id: str, user_email: str = Depends(get_current_user)):
    drive_service, _ = create_services()
    try:
        # First verify the user owns the document
        all_docs = list_files(drive_service)
        doc = next((doc for doc in all_docs if doc['id'] == doc_id), None)

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if not any(owner.get("emailAddress") == user_email for owner in doc.get("owners", [])):
            raise HTTPException(status_code=403, detail="Not authorized to remove this document")

        # Get all permissions for the document
        permissions_response = drive_service.permissions().list(
            fileId=doc_id,
            fields="permissions(id,emailAddress,role,type)",
            supportsAllDrives=True
        ).execute()

        # Find and remove the service account's permission
        service_account_email = os.getenv('AGENT_ID')  # Make sure this env var is set
        removed = False

        for permission in permissions_response.get('permissions', []):
            if permission.get('emailAddress') == service_account_email:
                try:
                    drive_service.permissions().delete(
                        fileId=doc_id,
                        permissionId=permission['id'],
                        supportsAllDrives=True
                    ).execute()
                    removed = True
                    break
                except Exception as e:
                    print(f"Error removing permission: {e}")
                    raise

        if not removed:
            print(f"No permission found for {service_account_email}")
            print("Available permissions:", permissions_response.get('permissions'))
            raise HTTPException(
                status_code=404,
                detail="Service account permission not found"
            )

        return {"status": "success", "message": "Document access removed"}
    except Exception as e:
        print(f"Error removing document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error removing document access: {str(e)}"
        )
