from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from DbContext.database import Base


class Rol(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
    
    # Relaciones
    miembros = relationship("MiembroEmpresa", back_populates="rol")

