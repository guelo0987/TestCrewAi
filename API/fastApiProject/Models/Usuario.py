from sqlalchemy import Column, UUID, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from DbContext.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    estado = Column(String(20), nullable=False, default="activo")  # activo, inactivo, etc.
    ultimo_login = Column(DateTime(timezone=False), nullable=True)
    creado_en = Column(DateTime(timezone=False), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    empresas = relationship("MiembroEmpresa", back_populates="usuario")
    posts_creados = relationship("Post", back_populates="creador")

