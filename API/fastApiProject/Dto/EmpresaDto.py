"""
DTOs para la gestión de empresas
"""
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Importar los tipos necesarios (al final del archivo para evitar circular imports)
from Dto.PostDto import ReferenciaEstiloResponse, CacheEmpresaResponse


class EmpresaResponse(BaseModel):
    """DTO de respuesta para empresa"""
    id: UUID
    nombre: str
    descripcion: Optional[str]
    logo_url: Optional[str]
    colores_marca: Optional[dict]
    creado_en: datetime
    actualizado_en: datetime
    
    class Config:
        from_attributes = True


class MiEmpresaCompletaResponse(BaseModel):
    """DTO completo con empresa, referencias y cache"""
    empresa: EmpresaResponse
    referencias: List[ReferenciaEstiloResponse]  # Lista de referencias con sus datos
    cache: Optional[CacheEmpresaResponse] = None  # Cache si existe
    total_referencias: int
    tiene_cache: bool

