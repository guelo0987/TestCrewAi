"""
Modelo para el cache del style_guide de cada empresa.
Almacena el análisis de las referencias para evitar re-procesar.
"""
from sqlalchemy import Column, UUID, Text, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from DbContext.database import Base


class CacheEmpresa(Base):
    __tablename__ = "cache_empresas"
    
    # empresa_id es la PK (una empresa = un cache)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), primary_key=True)
    style_guide = Column(Text, nullable=True)           # El análisis completo de las referencias
    referencias_hash = Column(String(64), nullable=True) # Hash MD5 de las referencias actuales
    actualizado_en = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="cache")

