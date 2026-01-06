"""
Servicio para gestión de almacenamiento en Cloudflare R2
Contiene toda la lógica de negocio relacionada con gestión de referencias.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict

from Models import ReferenciaEstilo, CacheEmpresa, Empresa
from Dto.PostDto import ReferenciaEstiloResponse
from Utils.r2_storage import (
    delete_image_from_r2,
    list_images_in_folder
)


class StorageService:
    """Servicio para gestionar almacenamiento de archivos"""
    
    @staticmethod
    def delete_referencia_images(
        db: Session,
        referencia: ReferenciaEstilo
    ) -> None:
        """
        Elimina las imágenes de R2 asociadas a una referencia.
        
        Args:
            db: Sesión de base de datos
            referencia: Referencia de estilo
        """
        if referencia.imagenes_urls:
            for url in referencia.imagenes_urls:
                try:
                    # Extraer el filename de la URL
                    if "cdn.ferreteriagigante.com" in url:
                        filename = url.split("cdn.ferreteriagigante.com/")[-1]
                        delete_image_from_r2(filename)
                except Exception:
                    pass  # Continuar aunque falle la eliminación de una imagen
    
    @staticmethod
    def refresh_referencias_from_r2(
        db: Session,
        empresa: Empresa,
        folder_path: str = "referencias/"
    ) -> Dict:
        """
        Recarga las referencias de estilo desde R2.
        
        Este método:
        1. Lista todas las imágenes de la carpeta especificada en R2
        2. Elimina las referencias existentes de la empresa
        3. Crea nuevas referencias con las URLs actualizadas
        4. Invalida el cache
        
        Args:
            db: Sesión de base de datos
            empresa: Empresa para la cual recargar las referencias
            folder_path: Ruta de la carpeta en R2 (default: "referencias")
            
        Returns:
            Dict con información sobre las referencias recargadas
            
        Raises:
            HTTPException: Si hay error al recargar
        """
        try:
            # 1. Listar imágenes de la carpeta en R2
            referencias_urls = list_images_in_folder(folder_path)
            
            if not referencias_urls:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No se encontraron imágenes en la carpeta '{folder_path}' de R2"
                )
            
            # 2. Eliminar referencias existentes
            referencias_anteriores = db.query(ReferenciaEstilo).filter(
                ReferenciaEstilo.empresa_id == empresa.id
            ).all()
            
            # Eliminar imágenes de R2 si existen (solo si fueron subidas por el cliente)
            # Las de la carpeta default no se eliminan porque son compartidas
            for ref in referencias_anteriores:
                if ref.imagenes_urls:
                    for url in ref.imagenes_urls:
                        try:
                            # Solo eliminar si no es de la carpeta default
                            if "referencias/" not in url:
                                filename = url.split("cdn.ferreteriagigante.com/")[-1] if "cdn.ferreteriagigante.com" in url else None
                                if filename:
                                    delete_image_from_r2(filename)
                        except Exception:
                            pass
            
            # Eliminar referencias de la base de datos
            db.query(ReferenciaEstilo).filter(
                ReferenciaEstilo.empresa_id == empresa.id
            ).delete()
            
            # 3. Invalidar el cache
            db.query(CacheEmpresa).filter(
                CacheEmpresa.empresa_id == empresa.id
            ).delete()
            
            # 4. Crear nueva referencia con las URLs actualizadas
            nueva_referencia = ReferenciaEstilo(
                empresa_id=empresa.id,
                imagenes_urls=referencias_urls
            )
            db.add(nueva_referencia)
            db.commit()
            db.refresh(nueva_referencia)
            
            return {
                "message": f"Referencias recargadas exitosamente desde '{folder_path}'",
                "referencia": ReferenciaEstiloResponse.model_validate(nueva_referencia),
                "total_imagenes": len(referencias_urls),
                "folder_path": folder_path
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al recargar referencias: {str(e)}"
            )


# Instancia global del servicio
storage_service = StorageService()

