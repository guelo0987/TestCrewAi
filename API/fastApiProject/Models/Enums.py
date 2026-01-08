"""
Enums para el sistema de generación de posts
"""
import enum


class TipoContenido(str, enum.Enum):
    """
    Tipo de contenido del post.
    
    IMPORTANTE: Los valores deben coincidir EXACTAMENTE con el enum de la base de datos.
    La base de datos usa valores en inglés en mayúsculas.
    """
    SINGLE = "SINGLE"           # Un solo producto
    MULTI = "MULTI"             # Múltiples productos (1-4)
    SCRATCH = "SCRATCH"         # Sin producto, solo mensaje
    EXISTING = "EXISTING"       # Post ya existente (para programar)


class ModoEstilo(str, enum.Enum):
    """Modo de estilo para la generación"""
    REFERENCE = "reference"   # Copia exacta del estilo de referencias
    CREATIVE = "creative"     # Ambiente contextual creativo


class EstadoPost(str, enum.Enum):
    """
    Estado del post en el flujo de trabajo.
    
    IMPORTANTE: Los valores deben coincidir EXACTAMENTE con el enum de la base de datos.
    La base de datos usa valores en inglés en mayúsculas.
    """
    DRAFT = "DRAFT"                 # Borrador, creado pero no finalizado
    SCHEDULED = "SCHEDULED"         # Programado para publicación futura
    READY = "READY"                 # Generado y listo para publicar
    PUBLISHED = "PUBLISHED"         # Ya publicado
    CANCELLED = "CANCELLED"         # Cancelado


class TipoVersion(str, enum.Enum):
    """
    Tipo de versión del post.
    
    IMPORTANTE: Los valores deben coincidir EXACTAMENTE con el enum de la base de datos.
    La base de datos usa valores en inglés en mayúsculas.
    """
    ORIGINAL = "ORIGINAL"           # Primera generación
    REGENERATION = "REGENERATION"   # Regeneración completa (diseño nuevo)
    EDIT = "EDIT"                   # Edición puntual (cambios específicos)
    VARIANT = "VARIANT"             # Variante (reference vs creative)

