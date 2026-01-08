"""
DTOs para el sistema de generación de posts
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS PARA VALIDACIÓN
# ============================================================================

class TipoContenidoEnum(str, Enum):
    PRODUCTO_UNICO = "producto_unico"
    MULTI_PRODUCTO = "multi_producto"
    SCRATCH = "scratch"


class ModoEstiloEnum(str, Enum):
    REFERENCE = "reference"
    CREATIVE = "creative"


class EstadoPostEnum(str, Enum):
    """
    Enum para el estado del post en los DTOs.
    
    IMPORTANTE: Los valores deben coincidir EXACTAMENTE con el enum de la base de datos.
    La base de datos usa valores en inglés en mayúsculas.
    """
    DRAFT = "DRAFT"                 # Borrador
    SCHEDULED = "SCHEDULED"         # Programado
    READY = "READY"                 # Listo para publicar
    PUBLISHED = "PUBLISHED"         # Publicado
    CANCELLED = "CANCELLED"         # Cancelado


class TipoVersionEnum(str, Enum):
    """
    IMPORTANTE: Los valores deben coincidir EXACTAMENTE con el enum de la base de datos.
    La base de datos usa valores en inglés en mayúsculas.
    """
    ORIGINAL = "ORIGINAL"
    REGENERATION = "REGENERATION"
    EDIT = "EDIT"
    VARIANT = "VARIANT"


# ============================================================================
# DTOs PARA REFERENCIAS DE ESTILO
# ============================================================================

class ReferenciaEstiloCreate(BaseModel):
    """DTO para crear una nueva referencia de estilo"""
    imagenes_urls: List[str] = Field(
        ..., 
        min_length=1,
        description="Lista de URLs de imágenes de referencia (JSON)"
    )


class ReferenciaEstiloResponse(BaseModel):
    """DTO de respuesta para referencia de estilo"""
    id: UUID
    empresa_id: UUID
    imagenes_urls: List[str]
    creado_en: datetime
    
    class Config:
        from_attributes = True


class ReferenciaEstiloUpdate(BaseModel):
    """DTO para actualizar una referencia de estilo"""
    imagenes_urls: Optional[List[str]] = None


class ReferenciasBatchCreate(BaseModel):
    """
    DTO para crear múltiples referencias de estilo a la vez.
    
    Funciona como si subieras una "carpeta" de referencias.
    Todas las imágenes se analizarán juntas para extraer el estilo visual.
    
    Ejemplo:
        {
            "imagenes_urls": [
                "https://storage.com/referencias/ref1.png",
                "https://storage.com/referencias/ref2.png",
                "https://storage.com/referencias/ref3.png"
            ],
            "reemplazar_existentes": false
        }
    """
    imagenes_urls: List[str] = Field(
        ..., 
        min_length=1,
        max_length=20,
        description="Lista de URLs de imágenes de referencia (1-20 imágenes)"
    )
    reemplazar_existentes: bool = Field(
        False,
        description="Si True, elimina las referencias anteriores. Si False, agrega a las existentes."
    )


class ReferenciasBatchResponse(BaseModel):
    """Respuesta al crear múltiples referencias"""
    total_creadas: int
    referencias: List[ReferenciaEstiloResponse]
    mensaje: str


# ============================================================================
# DTOs PARA CACHE DE EMPRESA
# ============================================================================

class CacheEmpresaResponse(BaseModel):
    """DTO de respuesta para el cache de la empresa"""
    empresa_id: UUID
    style_guide: Optional[str]
    referencias_hash: Optional[str]
    actualizado_en: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# DTOs PARA VERSIONES DE POSTS
# ============================================================================

class VersionPostResponse(BaseModel):
    """DTO de respuesta para versión de post"""
    id: UUID
    post_id: UUID
    version_padre_id: Optional[UUID]
    numero_version: int
    tipo_version: TipoVersionEnum
    variante: Optional[str]
    imagen_url: Optional[str]
    cambios_solicitados: Optional[str]
    creado_en: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# DTOs PARA POSTS - CREACIÓN
# ============================================================================

class PostCreateBase(BaseModel):
    """Base para crear posts"""
    request_usuario: str = Field(..., description="Solicitud del usuario para el post")
    nombre_interno: Optional[str] = Field(None, description="Nombre interno para identificar el post")
    modo_estilo: ModoEstiloEnum = Field(ModoEstiloEnum.CREATIVE, description="Modo de generación")
    generar_ambas_versiones: bool = Field(False, description="Si True, genera reference y creative")


class PostCreateProducto(PostCreateBase):
    """DTO para crear post con un producto"""
    imagen_producto_url: str = Field(..., description="URL de la imagen del producto")


class PostCreateMultiProducto(PostCreateBase):
    """DTO para crear post con múltiples productos"""
    imagenes_productos_urls: List[str] = Field(
        ..., 
        min_length=1, 
        max_length=4,
        description="URLs de las imágenes de productos (1-4)"
    )


class PostCreateScratch(PostCreateBase):
    """DTO para crear post sin producto (desde cero)"""
    pass  # Solo necesita request_usuario del base


class PostEditRequest(BaseModel):
    """DTO para editar un post existente"""
    cambios: str = Field(..., description="Descripción de los cambios a realizar")


class PostRegenerateRequest(BaseModel):
    """DTO para regenerar un post existente"""
    feedback: Optional[str] = Field("", description="Feedback opcional sobre qué mejorar")


# ============================================================================
# DTOs PARA POSTS - RESPUESTAS
# ============================================================================

class PostResponse(BaseModel):
    """DTO de respuesta completa para un post"""
    id: UUID
    empresa_id: UUID
    creado_por: UUID
    nombre_interno: Optional[str]
    request_usuario: str
    es_programado: bool
    tipo_contenido: TipoContenidoEnum
    modo_estilo: ModoEstiloEnum
    estado: EstadoPostEnum
    fecha_programada: Optional[datetime]
    fecha_publicacion: Optional[datetime]
    imagen_existente_url: Optional[str]
    version_elegida_id: Optional[UUID]
    creado_en: datetime
    actualizado_en: datetime
    
    class Config:
        from_attributes = True


class PostResponseWithVersions(PostResponse):
    """DTO de respuesta con versiones incluidas"""
    versiones: List[VersionPostResponse] = []
    version_elegida: Optional[VersionPostResponse] = None


class PostListResponse(BaseModel):
    """DTO para listado de posts"""
    posts: List[PostResponse]
    total: int
    pagina: int
    por_pagina: int


# ============================================================================
# DTOs PARA RESULTADOS DE GENERACIÓN
# ============================================================================

class GenerationResult(BaseModel):
    """Resultado de una generación de imagen"""
    status: str  # "success" o "error"
    version_id: Optional[UUID] = None
    imagen_url: Optional[str] = None
    mensaje: Optional[str] = None
    modo: Optional[str] = None


class GenerationBothResult(BaseModel):
    """Resultado de generación de ambas versiones"""
    reference: GenerationResult
    creative: GenerationResult


# ============================================================================
# DTOs PARA ACTUALIZACIÓN DE POSTS
# ============================================================================

class PostUpdateEstado(BaseModel):
    """DTO para actualizar el estado de un post"""
    estado: EstadoPostEnum


class PostSelectVersion(BaseModel):
    """DTO para seleccionar la versión elegida"""
    version_id: UUID


class PostSchedule(BaseModel):
    """DTO para programar un post"""
    fecha_programada: datetime

