from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models import Document, Department, UserGroup, User
from schemas import DashboardResponse, DashboardStats, DeptDocCount, RecentDocument

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):

    # ---- stat cards ----
    total_documents = db.scalar(select(func.count(Document.document_id))) or 0
    total_departments = db.scalar(select(func.count(Department.dept_id))) or 0
    total_user_groups = db.scalar(select(func.count(UserGroup.group_id))) or 0
    total_users = db.scalar(select(func.count(User.user_id))) or 0

    stats = DashboardStats(
        total_documents=total_documents,
        total_departments=total_departments,
        total_user_groups=total_user_groups,
        total_users=total_users,
    )

    # ---- docs by department (pie chart) ----
    dept_rows = db.execute(
        select(Department.dept_name, func.count(Document.document_id))
        .outerjoin(Document, Document.department_id == Department.dept_id)
        .group_by(Department.dept_name)
        .order_by(func.count(Document.document_id).desc())
    ).all()

    documents_by_department = [
        DeptDocCount(dept_name=row[0], count=row[1]) for row in dept_rows if row[1] > 0
    ]

    # ---- recent documents ----
    recent_rows = db.execute(
        select(
            Document.document_name,
            Department.dept_name,
            User.username,
            Document.upload_date,
        )
        .join(Department, Document.department_id == Department.dept_id)
        .join(User, Document.uploaded_by == User.user_id)
        .order_by(Document.upload_date.desc())
        .limit(5)
    ).all()

    recent_documents = [
        RecentDocument(
            document_name=row[0],
            department=row[1],
            uploaded_by=row[2],
            upload_date=row[3],
        )
        for row in recent_rows
    ]

    return DashboardResponse(
        stats=stats,
        documents_by_department=documents_by_department,
        recent_documents=recent_documents,
    )
