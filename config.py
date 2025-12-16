"""
Configuración del Sistema de Generación de Posts
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ModelConfig:
    """Configuración de modelos de Gemini"""
    TEXT_MODEL = "gemini-2.5-flash"
    IMAGE_GENERATION_MODEL = "gemini-2.0-flash-exp-image-generation"


@dataclass 
class InstagramConfig:
    """Configuración para posts de Instagram"""
    IMAGE_SIZE = (1080, 1080)
    ASPECT_RATIO = "1:1"
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']


@dataclass
class DNAExtractionConfig:
    """Configuración para extracción de ADN visual"""
    MAX_REFERENCE_IMAGES = 6  # Máximo de imágenes a analizar
    MAX_CONTEXT_IMAGES = 3    # Máximo de imágenes para contexto en generación
