from datetime import datetime
from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_documents: int
    total_departments: int
    total_user_groups: int
    total_users: int


class DeptDocCount(BaseModel):
    dept_name: str
    count: int


class RecentDocument(BaseModel):
    document_name: str
    department: str
    uploaded_by: str
    upload_date: datetime


class DashboardResponse(BaseModel):
    stats: DashboardStats
    documents_by_department: list[DeptDocCount]
    recent_documents: list[RecentDocument]


class DocumentRow(BaseModel):
    document_id: int
    document_name: str
    department: str
    uploaded_by: str
    upload_date: datetime
    status: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentRow]
    total: int
    page: int
    page_size: int


class DepartmentOut(BaseModel):
    dept_id: int
    dept_name: str


class UserOut(BaseModel):
    user_id: int
    username: str


class UserGroupOut(BaseModel):
    group_id: int
    group_name: str
