from sqlalchemy import Column, UUID, Integer, ForeignKey
from sqlalchemy.orm import relationship
from DbContext.database import Base


class MiembroEmpresa(Base):
    __tablename__ = "miembros_empresa"
    
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), primary_key=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), primary_key=True)
    rol_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="miembros")
    usuario = relationship("Usuario", back_populates="empresas")
    rol = relationship("Rol", back_populates="miembros")

