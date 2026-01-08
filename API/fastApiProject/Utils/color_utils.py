"""
Utilidades para manejo de colores de marca
"""

from typing import List, Optional, Any
from fastapi import HTTPException, status


def extract_colors_from_json(colores_marca: Optional[Any]) -> List[str]:
    """
    Extrae los colores de la marca desde el campo JSON de la base de datos.
    
    El campo colores_marca puede venir como:
    - Lista: ["#FF6B35", "#004E89", "#FFFFFF"]
    - Dict: {"primary": "#FF6B35", "secondary": "#004E89", "background": "#FFFFFF"}
    - Dict con otros nombres: {"color1": "#FF6B35", "color2": "#004E89", "color3": "#FFFFFF"}
    - None o vacío
    
    Args:
        colores_marca: Campo JSON de colores de la empresa
        
    Returns:
        Lista de colores en formato hex (strings). Si no hay colores, retorna lista vacía.
    """
    if not colores_marca:
        return []
    
    colors_list = []
    
    # Si es una lista, extraer directamente
    if isinstance(colores_marca, list):
        for color in colores_marca:
            if isinstance(color, str) and color.strip():
                colors_list.append(color.strip())
    
    # Si es un diccionario, extraer todos los valores que parezcan colores hex
    elif isinstance(colores_marca, dict):
        for key, value in colores_marca.items():
            if isinstance(value, str) and value.strip():
                # Verificar si parece un color hex (empieza con # y tiene 4-7 caracteres)
                color_str = value.strip()
                if color_str.startswith('#') and len(color_str) in [4, 5, 7, 9]:
                    colors_list.append(color_str)
                # También aceptar valores sin # si son hex válidos
                elif len(color_str) in [3, 4, 6, 8] and all(c in '0123456789ABCDEFabcdef' for c in color_str):
                    colors_list.append(f"#{color_str}")
    
    # Si es un string, intentar parsearlo como JSON
    elif isinstance(colores_marca, str):
        try:
            import json
            parsed = json.loads(colores_marca)
            return extract_colors_from_json(parsed)
        except:
            # Si no se puede parsear, tratarlo como un solo color
            if colores_marca.strip().startswith('#'):
                colors_list.append(colores_marca.strip())
    
    return colors_list


def ensure_colors_list(colores_marca: Optional[Any], empresa_nombre: str = "la empresa") -> List[str]:
    """
    Asegura que la lista de colores tenga al menos 3 elementos para los prompts.
    Los prompts requieren colors[0], colors[1], colors[2].
    
    Primero extrae los colores del JSON, luego completa si es necesario.
    Si no hay colores, lanza una excepción HTTP indicando que debe configurar los colores.
    
    Args:
        colores_marca: Campo JSON de colores de la empresa (puede ser lista, dict, None)
        empresa_nombre: Nombre de la empresa para el mensaje de error
        
    Returns:
        Lista con al menos 3 colores en formato hex
        
    Raises:
        HTTPException: Si no se encuentran colores en la configuración de la empresa
    """
    # Extraer colores del JSON
    colors = extract_colors_from_json(colores_marca)
    
    # Si no hay colores extraídos, lanzar error
    if not colors or len(colors) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La empresa '{empresa_nombre}' no tiene colores de marca configurados. "
                   f"Por favor, configure los colores de marca antes de generar posts. "
                   f"Los colores deben estar en formato JSON como lista: [\"#FF6B35\", \"#004E89\", \"#FFFFFF\"] "
                   f"o como diccionario: {{\"primary\": \"#FF6B35\", \"secondary\": \"#004E89\"}}"
        )
    
    # Si tiene 3 o más, tomar solo los primeros 3
    if len(colors) >= 3:
        return colors[:3]
    
    # Si tiene menos de 3, completar repitiendo el último color disponible
    # Esto mantiene la paleta de la marca sin introducir colores externos
    while len(colors) < 3:
        if colors:
            # Repetir el último color disponible para mantener consistencia de marca
            colors.append(colors[-1])
        else:
            # Este caso no debería ocurrir porque ya validamos arriba, pero por seguridad
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La empresa '{empresa_nombre}' no tiene suficientes colores de marca configurados. "
                       f"Se requieren al menos 3 colores en formato hex (ej: [\"#FF6B35\", \"#004E89\", \"#FFFFFF\"])."
            )
    
    return colors

