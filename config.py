"""
Configuración del Sistema de Generación de Posts
Mantén todos los valores configurables aquí.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


# ============================================================================
# MODOS DE GENERACIÓN
# ============================================================================

class GenerationMode(Enum):
    """Modos de generación disponibles"""
    REFERENCE = "reference"  # Copia exacta del estilo de referencias
    CREATIVE = "creative"    # Ambiente contextual basado en producto/mensaje
    SCRATCH = "scratch"      # Sin imagen de producto, genera todo desde el mensaje


# ============================================================================
# CONFIGURACIÓN DE EMPRESA
# ============================================================================

@dataclass
class CompanyConfig:
    """Configuración de la empresa/marca"""
    name: str
    description: str
    color_palette: List[str]
    logo_path: Optional[str] = None


# ============================================================================
# CONFIGURACIÓN DEL SISTEMA
# ============================================================================

@dataclass
class SystemConfig:
    """Configuración del sistema de generación"""
    
    # Modelos de Gemini
    vision_model: str = "gemini-2.5-flash"
    image_model: str = "gemini-2.5-flash-image"
    
    # Límites
    max_references: int = 20  # Máximo de referencias a usar (reduce tokens)
    
    # Cache
    cache_style_guide: bool = True  # Guardar style_guide en JSON
    cache_file: str = ".style_guide_cache.json"
    
    # Imagen
    aspect_ratio: str = "1:1"
    output_quality: int = 95


# ============================================================================
# CONFIGURACIÓN POR DEFECTO
# ============================================================================

DEFAULT_SYSTEM_CONFIG = SystemConfig()
