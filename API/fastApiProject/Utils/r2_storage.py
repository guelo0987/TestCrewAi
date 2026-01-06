"""
Utilidades para gestionar almacenamiento en Cloudflare R2
Compatibilidad S3 usando boto3
"""

import os
import uuid
import io
import boto3
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from PIL import Image

# Cargar variables de entorno
load_dotenv()

# Configuración desde .env (se cargarán cuando se necesiten)
R2_ACCOUNT_ID = None
R2_ACCESS_KEY_ID = None
R2_SECRET_ACCESS_KEY = None
R2_BUCKET_NAME = None
R2_CUSTOM_DOMAIN = None
s3_client = None


def _load_r2_config():
    """Carga la configuración de R2 desde variables de entorno"""
    global R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
    global R2_BUCKET_NAME, R2_CUSTOM_DOMAIN, s3_client
    
    # Solo cargar si no están ya cargadas
    if R2_ACCOUNT_ID is None:
        R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
        R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
        R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
        R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "creai")
        R2_CUSTOM_DOMAIN = os.getenv("R2_CUSTOM_DOMAIN", "cdn.ferreteriagigante.com")
    
    # Validar que las credenciales estén configuradas
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        raise ValueError(
            "Las credenciales de R2 no están configuradas. "
            "Asegúrate de tener R2_ACCOUNT_ID, R2_ACCESS_KEY_ID y R2_SECRET_ACCESS_KEY en tu .env"
        )
    
    # Configurar cliente S3 para R2 solo si no está configurado
    if s3_client is None:
        s3_client = boto3.client(
            service_name='s3',
            endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name='auto'  # R2 requiere 'auto'
        )
    
    return s3_client


def _get_s3_client():
    """Obtiene el cliente S3, inicializándolo si es necesario"""
    if s3_client is None:
        return _load_r2_config()
    return s3_client

# Tipos de archivo permitidos para imágenes
ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/webp',
    'image/gif'
}

# Extensiones permitidas
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

# Tamaño máximo de archivo (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB en bytes


def validate_image_file(file: UploadFile) -> None:
    """
    Valida que el archivo sea una imagen válida.
    
    Args:
        file: Archivo a validar
        
    Raises:
        HTTPException: Si el archivo no es válido
    """
    # Validar tipo de contenido
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Solo se aceptan: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Validar extensión
    if file.filename:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Extensión no permitida. Solo se aceptan: {', '.join(ALLOWED_EXTENSIONS)}"
            )


def generate_unique_filename(original_filename: str, prefix: Optional[str] = None) -> str:
    """
    Genera un nombre de archivo único para evitar colisiones.
    
    Args:
        original_filename: Nombre original del archivo
        prefix: Prefijo opcional (ej: 'referencias', 'productos')
        
    Returns:
        Nombre de archivo único con extensión
    """
    file_extension = os.path.splitext(original_filename)[1].lower()
    unique_id = str(uuid.uuid4())
    
    if prefix:
        return f"{prefix}/{unique_id}{file_extension}"
    return f"{unique_id}{file_extension}"


def upload_image_to_r2(
    file: UploadFile,
    folder: Optional[str] = None,
    custom_filename: Optional[str] = None
) -> dict:
    """
    Sube una imagen a Cloudflare R2 y retorna la URL pública.
    
    Args:
        file: Archivo a subir
        folder: Carpeta dentro del bucket (ej: 'referencias', 'productos')
        custom_filename: Nombre personalizado (opcional, si no se proporciona se genera uno único)
        
    Returns:
        Dict con:
            - url: URL pública de la imagen
            - filename: Nombre del archivo en R2
            - size: Tamaño del archivo en bytes
            
    Raises:
        HTTPException: Si hay error al subir
    """
    try:
        # Validar archivo
        validate_image_file(file)
        
        # Leer contenido del archivo
        file_content = file.file.read()
        file_size = len(file_content)
        
        # Validar tamaño
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo es demasiado grande. Tamaño máximo: {MAX_FILE_SIZE / (1024*1024):.1f} MB"
            )
        
        # Generar nombre de archivo
        if custom_filename:
            filename = custom_filename
        else:
            prefix = folder if folder else None
            filename = generate_unique_filename(file.filename or "image", prefix)
        
        # Resetear el puntero del archivo para leerlo de nuevo
        file.file.seek(0)
        
        # Obtener cliente S3 (inicializa si es necesario)
        client = _get_s3_client()
        
        # Subir a R2
        client.upload_fileobj(
            file.file,
            R2_BUCKET_NAME,  # Se carga en _load_r2_config()
            filename,
            ExtraArgs={
                'ContentType': file.content_type,
                'CacheControl': 'max-age=31536000'  # Cache por 1 año
            }
        )
        
        # Construir URL pública usando el dominio personalizado
        public_url = f"https://{R2_CUSTOM_DOMAIN}/{filename}"  # Se carga en _load_r2_config()
        
        return {
            "url": public_url,
            "filename": filename,
            "size": file_size,
            "content_type": file.content_type
        }
        
    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de credenciales R2. Verifica tu configuración."
        )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir archivo a R2: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )


def upload_multiple_images_to_r2(
    files: List[UploadFile],
    folder: Optional[str] = None
) -> List[dict]:
    """
    Sube múltiples imágenes a R2.
    
    Args:
        files: Lista de archivos a subir
        folder: Carpeta dentro del bucket
        
    Returns:
        Lista de dicts con información de cada archivo subido
    """
    results = []
    
    for file in files:
        try:
            result = upload_image_to_r2(file, folder=folder)
            results.append({
                "success": True,
                "original_filename": file.filename,
                **result
            })
        except HTTPException as e:
            results.append({
                "success": False,
                "original_filename": file.filename,
                "error": e.detail
            })
        except Exception as e:
            results.append({
                "success": False,
                "original_filename": file.filename,
                "error": str(e)
            })
    
    return results


def delete_image_from_r2(filename: str) -> bool:
    """
    Elimina una imagen de R2.
    
    Args:
        filename: Nombre del archivo en R2 (con o sin prefijo de carpeta)
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
        
    Raises:
        HTTPException: Si hay error al eliminar
    """
    try:
        client = _get_s3_client()
        client.delete_object(Bucket=R2_BUCKET_NAME, Key=filename)  # R2_BUCKET_NAME se carga en _load_r2_config()
        return True
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar archivo de R2: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )


def delete_multiple_images_from_r2(filenames: List[str]) -> dict:
    """
    Elimina múltiples imágenes de R2.
    
    Args:
        filenames: Lista de nombres de archivos a eliminar
        
    Returns:
        Dict con estadísticas de eliminación
    """
    deleted = []
    failed = []
    
    for filename in filenames:
        try:
            delete_image_from_r2(filename)
            deleted.append(filename)
        except Exception as e:
            failed.append({"filename": filename, "error": str(e)})
    
    return {
        "deleted": deleted,
        "failed": failed,
        "total_deleted": len(deleted),
        "total_failed": len(failed)
    }


def get_public_url(filename: str) -> str:
    """
    Genera la URL pública de un archivo en R2.
    
    Args:
        filename: Nombre del archivo en R2
        
    Returns:
        URL pública completa
    """
    # Asegurar que la configuración esté cargada
    _get_s3_client()  # Esto carga la configuración si no está cargada
    return f"https://{R2_CUSTOM_DOMAIN}/{filename}"


def check_file_exists(filename: str) -> bool:
    """
    Verifica si un archivo existe en R2.
    
    Args:
        filename: Nombre del archivo a verificar
        
    Returns:
        True si existe, False en caso contrario
    """
    try:
        client = _get_s3_client()
        client.head_object(Bucket=R2_BUCKET_NAME, Key=filename)  # R2_BUCKET_NAME se carga en _load_r2_config()
        return True
    except ClientError:
        return False


def upload_pil_image_to_r2(
    pil_image,
    folder: str = "posts",
    custom_filename: Optional[str] = None,
    format: str = "PNG"
) -> dict:
    """
    Sube una imagen PIL directamente a Cloudflare R2.
    
    Args:
        pil_image: Imagen PIL (PIL.Image)
        folder: Carpeta dentro del bucket (default: "posts")
        custom_filename: Nombre personalizado (opcional, si no se proporciona se genera uno único)
        format: Formato de la imagen (PNG, JPEG, etc.)
        
    Returns:
        Dict con:
            - url: URL pública de la imagen
            - filename: Nombre del archivo en R2
            - size: Tamaño del archivo en bytes
            
    Raises:
        HTTPException: Si hay error al subir
    """
    try:
        # Convertir imagen PIL a bytes
        buffer = io.BytesIO()
        
        # Convertir RGBA a RGB si es necesario para JPEG
        if format.upper() == "JPEG" and pil_image.mode in ('RGBA', 'P'):
            # Crear fondo blanco para imágenes con transparencia
            rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
            if pil_image.mode == 'RGBA':
                rgb_image.paste(pil_image, mask=pil_image.split()[3])  # Usar canal alpha como máscara
            else:
                rgb_image.paste(pil_image)
            pil_image = rgb_image
        
        # Guardar imagen en buffer
        pil_image.save(buffer, format=format, quality=95)
        buffer.seek(0)
        image_bytes = buffer.read()
        file_size = len(image_bytes)
        
        # Generar nombre de archivo
        if custom_filename:
            filename = custom_filename
        else:
            unique_id = str(uuid.uuid4())
            extension = format.lower() if format.lower() != 'jpeg' else 'jpg'
            # Asegurar que la carpeta termine con /
            if not folder.endswith('/'):
                folder = folder + '/'
            filename = f"{folder}{unique_id}.{extension}"
        
        # Obtener cliente S3
        client = _get_s3_client()
        
        # Determinar content type
        content_type_map = {
            'PNG': 'image/png',
            'JPEG': 'image/jpeg',
            'JPG': 'image/jpeg',
            'WEBP': 'image/webp'
        }
        content_type = content_type_map.get(format.upper(), 'image/png')
        
        # Subir a R2
        buffer.seek(0)  # Resetear buffer para subir
        client.upload_fileobj(
            buffer,
            R2_BUCKET_NAME,
            filename,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000'  # Cache por 1 año
            }
        )
        
        # Construir URL pública
        public_url = get_public_url(filename)
        
        return {
            "url": public_url,
            "filename": filename,
            "size": file_size,
            "content_type": content_type
        }
        
    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de credenciales R2. Verifica tu configuración."
        )
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir imagen a R2: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al subir imagen: {str(e)}"
        )


def list_images_in_folder(folder_path: str = "referencias/") -> List[str]:
    """
    Lista todas las URLs públicas de imágenes en una carpeta de R2.
    
    Args:
        folder_path: Ruta de la carpeta en R2 (ej: "referencias/")
        
    Returns:
        Lista de URLs públicas de las imágenes encontradas
        
    Raises:
        HTTPException: Si hay error al listar
    """
    try:
        client = _get_s3_client()
        
        # Asegurar que la carpeta termine con /
        if not folder_path.endswith('/'):
            folder_path = folder_path + '/'
        
        # Listar objetos en la carpeta
        response = client.list_objects_v2(
            Bucket=R2_BUCKET_NAME,
            Prefix=folder_path
        )
        
        # Filtrar solo imágenes y generar URLs públicas
        image_urls = []
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                # Filtrar solo archivos (no carpetas) y que sean imágenes
                if not key.endswith('/') and any(key.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                    public_url = get_public_url(key)
                    image_urls.append(public_url)
        
        return image_urls
        
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar imágenes de R2: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )

