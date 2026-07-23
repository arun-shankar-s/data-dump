from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class UserGroup(Base):
    __tablename__ = "user_group"

    group_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_name: Mapped[str] = mapped_column(String(100), nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="group")


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("user_group.group_id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    group: Mapped["UserGroup"] = relationship(back_populates="users")
    documents_uploaded: Mapped[list["Document"]] = relationship(back_populates="uploader")


class Department(Base):
    __tablename__ = "department"

    dept_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dept_name: Mapped[str] = mapped_column(String(100), nullable=False)

    documents: Mapped[list["Document"]] = relationship(back_populates="department")


class Document(Base):
    __tablename__ = "document"

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("department.dept_id"))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("user.user_id"))
    upload_date: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(50), default="active")

    department: Mapped["Department"] = relationship(back_populates="documents")
    uploader: Mapped["User"] = relationship(back_populates="documents_uploaded")


class DocumentPermission(Base):
    __tablename__ = "document_permission"

    permission_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.document_id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("user_group.group_id"))
    can_view: Mapped[bool] = mapped_column(Boolean, default=True)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
