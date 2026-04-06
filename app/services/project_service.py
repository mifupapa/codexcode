"""プロジェクトの永続化・取得・状態管理を担うサービス。
JSON ファイルで保存し、サーバー再起動後も復元できる。"""
from __future__ import annotations
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models import Page, Project

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
PROJECTS_DIR = DATA_DIR / "projects"


def _project_path(project_id: str) -> Path:
    return PROJECTS_DIR / project_id / "project.json"


def _images_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id / "images"


def _audio_dir(project_id: str) -> Path:
    return PROJECTS_DIR / project_id / "audio"


def save(project: Project) -> None:
    path = _project_path(project.project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    _images_dir(project.project_id).mkdir(exist_ok=True)
    _audio_dir(project.project_id).mkdir(exist_ok=True)
    project.updated_at = datetime.utcnow()
    path.write_text(project.model_dump_json(indent=2), encoding="utf-8")


def load(project_id: str) -> Optional[Project]:
    path = _project_path(project_id)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Project(**data)


def list_all() -> list[Project]:
    projects: list[Project] = []
    if not PROJECTS_DIR.exists():
        return projects
    for d in sorted(PROJECTS_DIR.iterdir()):
        if d.is_dir():
            p = load(d.name)
            if p:
                projects.append(p)
    return projects


def delete(project_id: str) -> bool:
    path = PROJECTS_DIR / project_id
    if path.exists():
        shutil.rmtree(path)
        return True
    return False


def get_page(project: Project, page_id: str) -> Optional[Page]:
    for p in project.pages:
        if p.page_id == page_id:
            return p
    return None


def update_page(project: Project, page: Page) -> None:
    page.updated_at = datetime.utcnow()
    for i, p in enumerate(project.pages):
        if p.page_id == page.page_id:
            project.pages[i] = page
            break
    save(project)


def images_dir(project_id: str) -> Path:
    return _images_dir(project_id)


def audio_dir(project_id: str) -> Path:
    return _audio_dir(project_id)
