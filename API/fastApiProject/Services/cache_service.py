"""
Servicio para manejar el cache del style_guide en la base de datos
"""

import hashlib
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from Models import ReferenciaEstilo, CacheEmpresa


class CacheService:
    """Servicio para manejar el cache del style_guide en la base de datos"""
    
    @staticmethod
    def get_references_hash(referencias: List[ReferenciaEstilo]) -> str:
        """
        Genera un hash MD5 basado en las referencias actuales.
        
        El hash se calcula usando:
        - ID de cada referencia
        - URLs de las imágenes (ordenadas para consistencia)
        
        Esto permite detectar cuando las referencias cambian y invalidar el cache.
        """
        if not referencias:
            return hashlib.md5(b"").hexdigest()
        
        # Ordenar por id para consistencia
        sorted_refs = sorted(referencias, key=lambda x: str(x.id))
        
        # Construir string con información de referencias
        # imagenes_urls es un JSON (lista), convertir a string ordenado para el hash
        refs_info_parts = []
        for r in sorted_refs:
            if r.imagenes_urls:
                # Ordenar URLs para consistencia
                sorted_urls = sorted(r.imagenes_urls)
                refs_info_parts.append(f"{r.id}:{','.join(sorted_urls)}")
        
        refs_info = "|".join(refs_info_parts)
        return hashlib.md5(refs_info.encode()).hexdigest()
    
    @staticmethod
    def get_cached_style_guide(db: Session, empresa_id: UUID) -> Optional[str]:
        """Obtiene el style_guide del cache si es válido"""
        cache = db.query(CacheEmpresa).filter(CacheEmpresa.empresa_id == empresa_id).first()
        if not cache or not cache.style_guide:
            return None
        
        # Verificar que el hash coincida con las referencias actuales
        referencias = db.query(ReferenciaEstilo).filter(
            ReferenciaEstilo.empresa_id == empresa_id
        ).all()
        
        current_hash = CacheService.get_references_hash(referencias)
        if cache.referencias_hash == current_hash:
            return cache.style_guide
        
        return None
    
    @staticmethod
    def save_style_guide(db: Session, empresa_id: UUID, style_guide: str, referencias: List[ReferenciaEstilo]):
        """
        Guarda el style_guide en el cache de la base de datos.
        
        El campo actualizado_en se actualiza automáticamente por SQLAlchemy (onupdate=func.now())
        """
        cache = db.query(CacheEmpresa).filter(CacheEmpresa.empresa_id == empresa_id).first()
        
        # Calcular hash de las referencias actuales
        referencias_hash = CacheService.get_references_hash(referencias)
        
        if cache:
            # Actualizar cache existente
            cache.style_guide = style_guide
            cache.referencias_hash = referencias_hash
        else:
            # Crear nuevo cache
            cache = CacheEmpresa(
                empresa_id=empresa_id,
                style_guide=style_guide,
                referencias_hash=referencias_hash
            )
            db.add(cache)
        
        db.commit()
        print(f"💾 Cache guardado para empresa {empresa_id} (hash: {referencias_hash[:8]}...)")

