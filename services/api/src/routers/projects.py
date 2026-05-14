"""Developlus API — Projects Router"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

from src.dependencies import CurrentUser, DBSession
from src.models import Project, ProjectSurveyData
from src.schemas import ProjectCreate, ProjectResponse, SuccessResponse

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
