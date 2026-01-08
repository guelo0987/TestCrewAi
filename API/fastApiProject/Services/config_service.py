"""
Configuración del Sistema de Generación de Posts
"""


class SystemConfig:
    """Configuración del sistema de generación"""
    vision_model: str = "gemini-2.5-flash"
    image_model: str = "gemini-2.5-flash-image"
    max_references: int = 20
    aspect_ratio: str = "1:1"
    output_quality: int = 95

