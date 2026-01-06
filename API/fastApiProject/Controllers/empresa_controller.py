"""
Controller para gestionar la empresa del usuario actual
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from DbContext.database import get_db
from Models import Usuario
from Dto.EmpresaDto import EmpresaResponse, MiEmpresaCompletaResponse
from Dto.PostDto import ReferenciaEstiloResponse, CacheEmpresaResponse
from Services.empresa_service import empresa_service
from Services.storage_service import storage_service
from Utils.jwt_handler import get_current_user

router = APIRouter(prefix="/empresas", tags=["Empresas"])


@router.get("/mi-empresa", response_model=EmpresaResponse)
async def obtener_mi_empresa(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene la información de tu empresa.
    
    Retorna los datos básicos de la empresa asociada a tu cuenta.
    """
    return empresa_service.get_empresa_info(db, current_user)


@router.get("/mi-empresa/referencias", response_model=List[ReferenciaEstiloResponse])
async def obtener_mis_referencias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene todas las referencias de estilo de tu empresa.
    
    Las referencias son las imágenes que definen el estilo visual
    de los posts que se generan para tu empresa.
    """
    return empresa_service.get_empresa_referencias(db, current_user)


@router.get("/mi-empresa/cache", response_model=CacheEmpresaResponse)
async def obtener_mi_cache(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene el cache del style_guide de tu empresa.
    
    El cache contiene el análisis del estilo visual extraído de tus referencias.
    Si no existe cache, significa que aún no se ha generado ningún post o
    que las referencias fueron modificadas recientemente.
    """
    return empresa_service.get_empresa_cache(db, current_user)


@router.get("/mi-empresa/completa", response_model=MiEmpresaCompletaResponse)
async def obtener_mi_empresa_completa(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene toda la información de tu empresa en un solo endpoint:
    - Datos de la empresa
    - Referencias de estilo
    - Cache del style_guide (si existe)
    
    Útil para obtener toda la información de tu empresa de una vez.
    """
    return empresa_service.get_empresa_completa(db, current_user)


@router.post("/mi-empresa/referencias/refresh")
async def refrescar_mis_referencias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Recarga las referencias de estilo desde la carpeta 'referencias/' en R2.
    
    Este endpoint:
    - Lista todas las imágenes actuales de la carpeta en R2
    - Elimina las referencias existentes de tu empresa
    - Crea nuevas referencias con las URLs actualizadas
    - Invalida el cache para que se regenere con las nuevas referencias
    
    Útil cuando se agregan nuevas imágenes a la carpeta default en R2 y quieres
    actualizar las referencias de tu empresa.
    
    **Nota:** Este botón de refresh solo actualiza las referencias desde R2.
    No puedes subir nuevas imágenes, solo recargar las que están en la carpeta default.
    """
    empresa = empresa_service.get_user_empresa(db, current_user)
    return storage_service.refresh_referencias_from_r2(db, empresa)

