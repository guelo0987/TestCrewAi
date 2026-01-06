"""
Modelo para los posts de Instagram.
Cada post puede tener múltiples versiones (original, regeneraciones, ediciones).
"""
from sqlalchemy import Column, UUID, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from DbContext.database import Base
from .Enums import TipoContenido, ModoEstilo, EstadoPost


class Post(Base):
    __tablename__ = "posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    creado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    
    # Información del post
    nombre_interno = Column(String(200), nullable=True)     # Nombre para identificar internamente
    request_usuario = Column(Text, nullable=False)           # Solicitud original del usuario
    
    # Configuración de generación
    es_programado = Column(Boolean, default=False)
    tipo_contenido = Column(SQLEnum(TipoContenido), nullable=False, default=TipoContenido.SINGLE)
    modo_estilo = Column(SQLEnum(ModoEstilo), nullable=False, default=ModoEstilo.CREATIVE)
    
    # Estado del post
    estado = Column(SQLEnum(EstadoPost), nullable=False, default=EstadoPost.DRAFT)
    
    # Fechas de programación/publicación
    fecha_programada = Column(DateTime(timezone=False), nullable=True)
    fecha_publicacion = Column(DateTime(timezone=False), nullable=True)
    
    # Imágenes de productos (URLs en JSON array)
    # Para PRODUCTO_UNICO: ["url1"]
    # Para MULTI_PRODUCTO: ["url1", "url2", "url3", "url4"]
    # Para SCRATCH: null o []
    imagenes_productos = Column(JSON, nullable=True)
    
    # Si es edición/regeneración de un post existente
    imagen_existente_url = Column(Text, nullable=True)
    
    # Versión elegida/aprobada (FK a versiones_posts)
    version_elegida_id = Column(UUID(as_uuid=True), ForeignKey("versiones_posts.id"), nullable=True)
    
    # Timestamps
    creado_en = Column(DateTime(timezone=False), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="posts")
    creador = relationship("Usuario", back_populates="posts_creados")
    versiones = relationship(
        "VersionPost", 
        back_populates="post",
        foreign_keys="VersionPost.post_id",
        cascade="all, delete-orphan"
    )
    version_elegida = relationship(
        "VersionPost",
        foreign_keys=[version_elegida_id],
        post_update=True  # Necesario para la relación circular
    )

