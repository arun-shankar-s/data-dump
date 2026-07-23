import os
import json
import uuid
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from database import get_db
from models import Document, Department, User, UserGroup, DocumentPermission
from schemas import DocumentListResponse, DocumentRow, DepartmentOut, UserOut, UserGroupOut

router = APIRouter(prefix="/api", tags=["documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    department_id: int | None = None,
    search: str | None = None,
    uploaded_by: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
):
    filters = []
    if department_id:
        filters.append(Document.department_id == department_id)
    if uploaded_by:
        filters.append(Document.uploaded_by == uploaded_by)
    if search:
        filters.append(Document.document_name.ilike(f"%{search}%"))
    if from_date:
        filters.append(Document.upload_date >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        filters.append(Document.upload_date <= datetime.combine(to_date, datetime.max.time()))

    base_query = (
        select(
            Document.document_id,
            Document.document_name,
            Department.dept_name,
            User.username,
            Document.upload_date,
            Document.status,
        )
        .join(Department, Document.department_id == Department.dept_id)
        .join(User, Document.uploaded_by == User.user_id)
    )
    if filters:
        base_query = base_query.where(and_(*filters))

    total = db.scalar(
        select(func.count()).select_from(base_query.subquery())
    ) or 0

    rows = db.execute(
        base_query.order_by(Document.upload_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    documents = [
        DocumentRow(
            document_id=row[0],
            document_name=row[1],
            department=row[2],
            uploaded_by=row[3],
            upload_date=row[4],
            status=row[5],
        )
        for row in rows
    ]

    return DocumentListResponse(documents=documents, total=total, page=page, page_size=page_size)


@router.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # remove file from disk if it exists (upload module writes here later)
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass

    db.delete(doc)
    db.commit()
    return {"status": "deleted", "document_id": document_id}


@router.get("/documents/{document_id}/download")
def download_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server yet — upload it first.")
    return FileResponse(doc.file_path, filename=doc.file_name)


@router.get("/documents/{document_id}/view")
def view_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on server yet — upload it first.")
    return FileResponse(doc.file_path)


@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db)):
    rows = db.execute(select(Department.dept_id, Department.dept_name).order_by(Department.dept_name)).all()
    return [DepartmentOut(dept_id=r[0], dept_name=r[1]) for r in rows]


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    rows = db.execute(select(User.user_id, User.username).order_by(User.username)).all()
    return [UserOut(user_id=r[0], username=r[1]) for r in rows]


@router.get("/user-groups", response_model=list[UserGroupOut])
def list_user_groups(db: Session = Depends(get_db)):
    rows = db.execute(select(UserGroup.group_id, UserGroup.group_name).order_by(UserGroup.group_id)).all()
    return [UserGroupOut(group_id=r[0], group_name=r[1]) for r in rows]


@router.post("/documents/upload", status_code=201)
async def upload_document(
    document_name: str = Form(...),
    department_id: int = Form(...),
    uploaded_by: int = Form(...),
    permissions: str = Form("[]"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # validate department + uploader exist
    if not db.get(Department, department_id):
        raise HTTPException(status_code=400, detail="Department not found")
    if not db.get(User, uploaded_by):
        raise HTTPException(status_code=400, detail="Uploader user not found")

    # validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    # validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 20MB limit")

    # save file to disk with a unique name (avoid collisions)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(contents)

    # insert document row
    doc = Document(
        document_name=document_name,
        department_id=department_id,
        file_name=file.filename,
        file_path=stored_path,
        uploaded_by=uploaded_by,
        status="active",
    )
    db.add(doc)
    db.flush()  # get doc.document_id before commit

    # insert permission rows
    try:
        perm_list = json.loads(permissions)
    except json.JSONDecodeError:
        perm_list = []

    for p in perm_list:
        db.add(DocumentPermission(
            document_id=doc.document_id,
            group_id=p["group_id"],
            can_view=p.get("can_view", True),
            can_edit=p.get("can_edit", False),
        ))

    db.commit()
    db.refresh(doc)

    return {"status": "uploaded", "document_id": doc.document_id, "document_name": doc.document_name}
