from sqlalchemy import Column, UUID, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from DbContext.database import Base


class Empresa(Base):
    __tablename__ = "empresas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)
    colores_marca = Column(JSON, nullable=True)  # Array de colores hex: ["#FF6B35", "#004E89", "#FFFFFF"]
    creado_en = Column(DateTime(timezone=False), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    miembros = relationship("MiembroEmpresa", back_populates="empresa")
    referencias_estilo = relationship("ReferenciaEstilo", back_populates="empresa", cascade="all, delete-orphan")
    cache = relationship("CacheEmpresa", back_populates="empresa", uselist=False, cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="empresa", cascade="all, delete-orphan")

