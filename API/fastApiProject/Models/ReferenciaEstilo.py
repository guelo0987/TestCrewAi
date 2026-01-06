"""
Modelo para las referencias de estilo de cada empresa.

CONCEPTO:
=========
Las referencias funcionan como una "carpeta" de imágenes de ejemplo que definen 
el estilo visual de los posts de la empresa. Todas las imágenes de referencia 
se analizan JUNTAS para extraer:

- Efectos de texto (outline, sombras, estilos de fuente)
- Tratamiento del logo (posición, tamaño, fondo)
- Estilo de fondo (colores, texturas, gradientes)
- Elementos promocionales (banners, badges, descuentos)
- Paleta de colores
- Patrones de layout

FLUJO:
======
1. El usuario sube múltiples imágenes de referencia (3-20 recomendado)
2. Gemini analiza TODAS las imágenes juntas
3. Se genera un "style_guide" que se guarda en cache
4. El style_guide se usa para generar posts con el mismo estilo

NOTAS:
======
- Las referencias deben tener un estilo CONSISTENTE entre ellas
- Se pueden agregar/quitar referencias en cualquier momento
- Al modificar referencias, se debe regenerar el cache
"""
from sqlalchemy import Column, UUID, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from DbContext.database import Base


class ReferenciaEstilo(Base):
    """
    Representa UNA imagen de referencia de estilo.
    Una empresa tiene MÚLTIPLES referencias que se analizan juntas.
    
    Ejemplo: Si tienes 10 posts anteriores de Instagram con un estilo consistente,
    subes las 10 imágenes como referencias y el sistema aprende ese estilo.
    """
    __tablename__ = "referencias_estilo"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    empresa_id = Column(UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False)
    
    # URL de la imagen de referencia (almacenada en tu storage: S3, GCS, etc.)
    # Nota: El nombre de la columna en la BD es 'imaganes_url' (con typo), pero usamos 'imagenes_urls' como alias
    imagenes_urls = Column("imaganes_url", JSON, nullable=False)
    


    creado_en = Column(DateTime(timezone=False), server_default=func.now())
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="referencias_estilo")

