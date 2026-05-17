"""Developlus API — Projects Router"""
import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

from src.dependencies import CurrentUser, DBSession
from src.models import Project, ProjectSurveyData, ChatHistory, StackRecommendation
from src.schemas import (
    ProjectCreate, ProjectResponse, SuccessResponse,
    ProjectChatRequest, ChatHistoryListResponse, StackRecommendationResponse
)
from src.services import chat_service

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectResponse])
async def list_projects(current_user: CurrentUser, db: DBSession):
    """
    Kullanıcıya ait tüm projeleri listeler.
    Her projenin anket (survey_complete) durumunu da dahil eder.
    """
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.survey_data))
        .where(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    
    response_list = []
    for proj in projects:
        # Pydantic schema validation için projeyi dict benzeri objeye çevirmiyoruz,
        # ancak survey_complete dinamik özelliğini Pydantic model dump sırasında yakalaması için
        # objeye monkey-patch yapıyoruz veya dict üzerinden Pydantic build edebiliriz.
        # En temizi, yeni bir dict oluşturarak ProjectResponse'a parse etmektir.
        survey_complete = False
        if proj.survey_data:
            survey_complete = proj.survey_data.survey_complete
            
        proj_dict = {
            "id": proj.id,
            "user_id": proj.user_id,
            "project_name": proj.project_name,
            "description": proj.description,
            "status": proj.status,
            "survey_complete": survey_complete,
            "created_at": proj.created_at,
            "updated_at": proj.updated_at
        }
        response_list.append(proj_dict)
        
    return response_list


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, current_user: CurrentUser, db: DBSession):
    """
    Yeni bir proje oluşturur.
    Proje oluşturulurken otomatik olarak boş bir anket verisi de oluşturulur.
    """
    new_project = Project(
        user_id=current_user.id,
        project_name=data.project_name,
        description=data.description
    )
    db.add(new_project)
    await db.flush()  # ID almak için
    
    # Anket kaydını başlat
    survey_data = ProjectSurveyData(
        project_id=new_project.id,
        responses={}
    )
    db.add(survey_data)
    
    await db.commit()
    await db.refresh(new_project)
    
    return {
        "id": new_project.id,
        "user_id": new_project.user_id,
        "project_name": new_project.project_name,
        "description": new_project.description,
        "status": new_project.status,
        "survey_complete": False,
        "created_at": new_project.created_at,
        "updated_at": new_project.updated_at
    }


@router.put("/{project_id}/survey", response_model=SuccessResponse)
async def update_survey(project_id: UUID, answers: dict, current_user: CurrentUser, db: DBSession):
    """Projeye ait anket yanıtlarını günceller ve survey_complete=True yapar."""
    # Önce kullanıcının bu projeye sahip olduğunu doğrula
    owner_check = await db.execute(
        select(Project.id).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    if owner_check.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Proje anketi bulunamadı")

    # SQL UPDATE — ORM instance'a atama yok, Column descriptor hatası yok
    await db.execute(
        update(ProjectSurveyData)
        .where(ProjectSurveyData.project_id == project_id)
        .values(responses=answers, survey_complete=True)
    )
    await db.commit()

    return SuccessResponse(message="Anket başarıyla kaydedildi")

@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(project_id: UUID, current_user: CurrentUser, db: DBSession):
    """
    Belirtilen projeyi siler.
    DB seviyesinde CASCADE olduğundan anketler, mesajlar vb. her şey silinecek.
    """
    # Önce projenin bu kullanıcıya ait olduğunu doğrula
    owner_check = await db.execute(
        select(Project.id).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    if owner_check.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proje bulunamadı veya silme yetkiniz yok"
        )

    # SQL DELETE — ORM instance fetch etmeden direkt sil
    await db.execute(
        delete(Project).where(Project.id == project_id)
    )
    await db.commit()

    return SuccessResponse(message="Proje başarıyla silindi")
@router.get("/{project_id}/chat", response_model=ChatHistoryListResponse)
async def get_project_chat(project_id: UUID, current_user: CurrentUser, db: DBSession):
    """Projenin mesaj geçmişini döner."""
    # Önce sahiplik kontrolü
    owner_check = await db.execute(
        select(Project.id).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    if owner_check.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")
        
    messages = await chat_service.get_project_messages(db, project_id)
    return {
        "project_id": project_id,
        "messages": messages,
        "total_count": len(messages)
    }

@router.post("/{project_id}/chat/stream")
async def stream_project_chat(
    project_id: UUID, 
    request: ProjectChatRequest, 
    current_user: CurrentUser, 
    db: DBSession
):
    """Proje bazlı AI danışmanlığı — Streaming SSE."""
    # Sahiplik kontrolü
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")

    # Survey verisini de context olarak alalım (opsiyonel ama akıllıca)
    survey_res = await db.execute(
        select(ProjectSurveyData).where(ProjectSurveyData.project_id == project_id)
    )
    survey = survey_res.scalar_one_or_none()
    survey_context = ""
    if survey and survey.responses:
        survey_context = f"\n\n## Proje Teknik Kısıtları (Anket Yanıtları):\n{json.dumps(survey.responses, ensure_ascii=False)}"

    async def event_generator():
        try:
            async for token in chat_service.stream_project_chat(
                db=db,
                project_id=project_id,
                user_id=UUID(str(current_user.id)),
                user_message=request.message,
                survey_context=survey_context,
            ):
                payload = json.dumps({"token": token}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            print(f"[stream_project_chat endpoint] error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.get("/{project_id}/stack", response_model=StackRecommendationResponse)
async def get_latest_stack(project_id: UUID, current_user: CurrentUser, db: DBSession):
    """Projenin en güncel stack önerisini döner."""
    # Sahiplik kontrolü
    owner_check = await db.execute(
        select(Project.id).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    if owner_check.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Proje bulunamadı")

    result = await db.execute(
        select(StackRecommendation)
        .where(StackRecommendation.project_id == project_id)
        .order_by(StackRecommendation.version.desc())
        .limit(1)
    )
    stack = result.scalar_one_or_none()
    if not stack:
        # Eğer hiç stack yoksa boş bir response dönelim veya 404
        raise HTTPException(status_code=404, detail="Bu proje için henüz bir stack önerisi oluşturulmamış.")
    
    return stack
