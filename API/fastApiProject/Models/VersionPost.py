"""
Modelo para las versiones de cada post.
Cada post puede tener múltiples versiones: original, regeneraciones, ediciones.
"""
from sqlalchemy import Column, UUID, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from DbContext.database import Base
from .Enums import TipoVersion


class VersionPost(Base):
    __tablename__ = "versiones_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    
    # Si esta versión se basó en otra (para regeneraciones/ediciones)
    version_padre_id = Column(UUID(as_uuid=True), ForeignKey("versiones_posts.id"), nullable=True)
    
    # Número de versión (1, 2, 3, etc.)
    numero_version = Column(Integer, nullable=False, default=1)
    
    # Tipo de versión
    tipo_version = Column(SQLEnum(TipoVersion), nullable=False, default=TipoVersion.ORIGINAL)
    
    # Variante dentro de la versión (ej: "reference", "creative")
    # Permite generar ambas versiones en una sola solicitud
    variante = Column(String(20), nullable=True)
    
    # URL de la imagen generada
    imagen_url = Column(Text, nullable=True)
    
    # Cambios solicitados (para ediciones/regeneraciones)
    cambios_solicitados = Column(Text, nullable=True)
    
    # Timestamp
    creado_en = Column(DateTime(timezone=False), server_default=func.now())
    
    # Relaciones
    post = relationship(
        "Post", 
        back_populates="versiones",
        foreign_keys=[post_id]
    )
    version_padre = relationship(
        "VersionPost", 
        remote_side=[id],
        foreign_keys=[version_padre_id]
    )

