from __future__ import annotations
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field
import uuid


PageStatus = Literal["pending", "processing", "done", "error"]


class Page(BaseModel):
    page_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order: int
    image_path: str
    ocr_text: str = ""
    ocr_status: PageStatus = "pending"
    tts_path: str = ""
    tts_status: PageStatus = "pending"
    drive_file_id: Optional[str] = None
    error_message: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Project(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    author: str = ""
    language: str = "ja"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    pages: list[Page] = []


# --- Request/Response schemas ---

class ProjectCreate(BaseModel):
    title: str
    author: str = ""
    language: str = "ja"


class ProjectResponse(BaseModel):
    project_id: str
    title: str
    author: str
    language: str
    created_at: datetime
    page_count: int
    done_count: int
    error_count: int


class PageResponse(BaseModel):
    page_id: str
    order: int
    ocr_text: str
    ocr_status: PageStatus
    tts_path: str
    tts_status: PageStatus
    drive_file_id: Optional[str]
    error_message: Optional[str]


class OcrResult(BaseModel):
    page_id: str
    ocr_text: str
    ocr_status: PageStatus
    error_message: Optional[str] = None


class TtsResult(BaseModel):
    page_id: str
    tts_path: str
    tts_status: PageStatus
    error_message: Optional[str] = None


class TextUpdate(BaseModel):
    ocr_text: str


class DriveResult(BaseModel):
    page_id: str
    drive_file_id: Optional[str]
    status: str
    message: str
