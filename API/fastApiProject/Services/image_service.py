"""
Servicio para cargar y procesar imágenes
"""

import io
from typing import Optional
from PIL import Image
import httpx


class ImageService:
    """Servicio para cargar imágenes desde URLs o UploadFiles"""
    
    @staticmethod
    async def load_image_from_url(url: str) -> Optional[Image.Image]:
        """Carga una imagen desde una URL (asíncrono)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                return img
        except Exception as e:
            print(f"❌ Error cargando imagen desde {url}: {e}")
            return None
    
    @staticmethod
    def load_image_from_url_sync(url: str) -> Optional[Image.Image]:
        """Carga una imagen desde una URL (síncrono)"""
        try:
            with httpx.Client() as client:
                response = client.get(url, timeout=30.0)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                return img
        except Exception as e:
            print(f"❌ Error cargando imagen desde {url}: {e}")
            return None
    
    @staticmethod
    def load_image_from_upload_file(file) -> Optional[Image.Image]:
        """
        Carga una imagen directamente desde un UploadFile de FastAPI.
        No guarda el archivo, solo lo lee en memoria.
        
        Args:
            file: UploadFile de FastAPI
            
        Returns:
            PIL Image o None si hay error
        """
        try:
            # Leer el contenido del archivo en memoria
            file_content = file.file.read()
            # Resetear el puntero para que pueda leerse de nuevo si es necesario
            file.file.seek(0)
            
            # Abrir imagen desde bytes
            img = Image.open(io.BytesIO(file_content))
            
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            return img
        except Exception as e:
            print(f"❌ Error cargando imagen desde UploadFile: {e}")
            return None
    
    @staticmethod
    def image_to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
        """Convierte una imagen PIL a bytes"""
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()

