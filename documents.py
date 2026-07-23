import os
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from database import get_db
from models import Document, Department, User
from schemas import DocumentListResponse, DocumentRow, DepartmentOut, UserOut

router = APIRouter(prefix="/api", tags=["documents"])


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
