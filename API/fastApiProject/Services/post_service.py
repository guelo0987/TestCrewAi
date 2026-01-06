"""
Servicio de Generación de Posts de Instagram
Contiene toda la lógica de generación conectada a la base de datos.
"""

import os
import io
import hashlib
import httpx
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from PIL import Image
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Google Gemini
from google import genai
from google.genai import types

# Modelos y DTOs
from Models import (
    Empresa, 
    ReferenciaEstilo, 
    CacheEmpresa, 
    Post, 
    VersionPost,
    TipoContenido,
    ModoEstilo,
    EstadoPost,
    TipoVersion
)
from Dto.PostDto import (
    ModoEstiloEnum,
    TipoContenidoEnum,
    GenerationResult
)

# Importar prompts desde el proyecto raíz
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from prompts import (
    ANALYZE_REFERENCES_PROMPT,
    ANALYZE_PRODUCT_BASIC_PROMPT,
    ANALYZE_PRODUCT_CONTEXT_PROMPT,
    ANALYZE_MESSAGE_PROMPT,
    ANALYZE_POST_FOR_REGENERATION_PROMPT,
    ANALYZE_MULTIPLE_PRODUCTS_PROMPT,
    ANALYZE_EDIT_REQUEST_PROMPT,
    REFERENCES_INSTRUCTION,
    LOGO_INSTRUCTION,
    PRODUCT_INSTRUCTION,
    POST_TO_EDIT_INSTRUCTION,
    get_user_intent_prompt,
    get_reference_prompt,
    get_creative_prompt,
    get_scratch_prompt,
    get_regeneration_prompt,
    get_multi_product_reference_prompt,
    get_multi_product_creative_prompt,
    get_multi_product_instruction,
    get_edit_post_prompt,
)

# Importar utilidades de R2
from Utils.r2_storage import upload_pil_image_to_r2

load_dotenv()


# ============================================================================
# CONFIGURACIÓN DEL SISTEMA
# ============================================================================

class SystemConfig:
    """Configuración del sistema de generación"""
    vision_model: str = "gemini-2.5-flash"
    image_model: str = "gemini-2.5-flash-image"
    max_references: int = 20
    aspect_ratio: str = "1:1"
    output_quality: int = 95


# ============================================================================
# CLIENTE GEMINI
# ============================================================================

class GeminiClient:
    """Cliente para Gemini API"""
    
    def __init__(self, config: SystemConfig = None):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.config = config or SystemConfig()
    
    def _pil_to_part(self, img: Image.Image) -> types.Part:
        """Convierte una imagen PIL a Part de Gemini"""
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return types.Part.from_bytes(
            mime_type="image/png",
            data=buffer.getvalue()
        )
    
    def analyze_with_images(self, prompt: str, images: List[Image.Image]) -> str:
        """Analiza imágenes con un prompt"""
        try:
            parts = [self._pil_to_part(img) for img in images]
            parts.append(types.Part.from_text(text=prompt))
            
            response = self.client.models.generate_content(
                model=self.config.vision_model,
                contents=[types.Content(role="user", parts=parts)]
            )
            return response.text
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return ""
    
    def analyze_text(self, prompt: str) -> str:
        """Análisis solo de texto"""
        try:
            response = self.client.models.generate_content(
                model=self.config.vision_model,
                contents=[types.Content(
                    role="user", 
                    parts=[types.Part.from_text(text=prompt)]
                )]
            )
            return response.text
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return ""
    
    def generate_image(self, parts: List[types.Part]) -> Optional[Image.Image]:
        """Genera imagen con configuración 1:1"""
        try:
            response = self.client.models.generate_content(
                model=self.config.image_model,
                contents=[types.Content(role="user", parts=parts)],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=types.ImageConfig(aspect_ratio=self.config.aspect_ratio),
                )
            )
            
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
                        return Image.open(io.BytesIO(part.inline_data.data))
            
            return None
            
        except Exception as e:
            print(f"❌ Error generando imagen: {e}")
            return None


# ============================================================================
# SERVICIO DE IMÁGENES (Carga desde URLs)
# ============================================================================

class ImageService:
    """Servicio para cargar imágenes desde URLs"""
    
    @staticmethod
    async def load_image_from_url(url: str) -> Optional[Image.Image]:
        """Carga una imagen desde una URL"""
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
    def image_to_bytes(img: Image.Image, format: str = "PNG") -> bytes:
        """Convierte una imagen PIL a bytes"""
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()
    
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


# ============================================================================
# HELPERS
# ============================================================================

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
    from fastapi import HTTPException, status
    
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


# ============================================================================
# SERVICIO DE CACHE
# ============================================================================

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
        Similar a main.py pero usando URLs de R2 en lugar de archivos locales.
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
            # actualizado_en se actualiza automáticamente por onupdate=func.now()
        else:
            # Crear nuevo cache
            cache = CacheEmpresa(
                empresa_id=empresa_id,
                style_guide=style_guide,
                referencias_hash=referencias_hash
                # actualizado_en se establece automáticamente por server_default=func.now()
            )
            db.add(cache)
        
        db.commit()
        print(f"💾 Cache guardado para empresa {empresa_id} (hash: {referencias_hash[:8]}...)")


# ============================================================================
# ANALIZADOR
# ============================================================================

class Analyzer:
    """Analizador de imágenes y texto"""
    
    def __init__(self, client: GeminiClient):
        self.client = client
    
    def deep_analyze_references(self, images: List[Image.Image]) -> str:
        """Análisis exhaustivo de referencias"""
        return self.client.analyze_with_images(ANALYZE_REFERENCES_PROMPT, images)
    
    def analyze_product_basic(self, product_image: Image.Image) -> str:
        """Análisis básico del producto"""
        return self.client.analyze_with_images(ANALYZE_PRODUCT_BASIC_PROMPT, [product_image])
    
    def analyze_product_for_context(self, product_image: Image.Image) -> str:
        """Analiza el producto para contexto creativo"""
        return self.client.analyze_with_images(ANALYZE_PRODUCT_CONTEXT_PROMPT, [product_image])
    
    def analyze_user_intent(self, request: str, empresa: Empresa) -> str:
        """Analiza la intención del usuario"""
        colors_list = ensure_colors_list(empresa.colores_marca, empresa.nombre)
        colors_str = ', '.join(colors_list)
        prompt = get_user_intent_prompt(
            empresa.nombre, 
            empresa.descripcion or "", 
            colors_str, 
            request
        )
        return self.client.analyze_text(prompt)
    
    def analyze_message_for_scratch(self, message: str, empresa: Empresa) -> str:
        """Analiza el mensaje para generar contenido desde cero"""
        prompt = ANALYZE_MESSAGE_PROMPT.format(
            message=message,
            company_name=empresa.nombre,
            company_description=empresa.descripcion or ""
        )
        return self.client.analyze_text(prompt)
    
    def analyze_post_for_regeneration(self, post_image: Image.Image) -> str:
        """Analiza un post existente para regenerarlo"""
        return self.client.analyze_with_images(ANALYZE_POST_FOR_REGENERATION_PROMPT, [post_image])
    
    def analyze_edit_request(self, edit_request: str) -> str:
        """Analiza la solicitud de edición"""
        prompt = ANALYZE_EDIT_REQUEST_PROMPT.format(edit_request=edit_request)
        return self.client.analyze_text(prompt)
    
    def analyze_multiple_products(self, product_images: List[Image.Image]) -> str:
        """Analiza múltiples productos"""
        num_products = len(product_images)
        prompt = ANALYZE_MULTIPLE_PRODUCTS_PROMPT.format(num_products=num_products)
        return self.client.analyze_with_images(prompt, product_images)
    
    def analyze_multiple_products_for_context(self, product_images: List[Image.Image]) -> str:
        """Analiza múltiples productos para contexto creativo"""
        contexts = []
        for i, img in enumerate(product_images, 1):
            context = self.client.analyze_with_images(ANALYZE_PRODUCT_CONTEXT_PROMPT, [img])
            contexts.append(f"PRODUCT {i}:\n{context}")
        return "\n\n".join(contexts)


# ============================================================================
# SERVICIO PRINCIPAL DE POSTS
# ============================================================================

class PostService:
    """Servicio principal para generación y gestión de posts"""
    
    def __init__(self):
        self.config = SystemConfig()
        self.gemini_client = GeminiClient(self.config)
        self.analyzer = Analyzer(self.gemini_client)
        self.image_service = ImageService()
    
    # =========================================================================
    # MÉTODOS DE INICIALIZACIÓN
    # =========================================================================
    
    async def get_or_create_style_guide(
        self, 
        db: Session, 
        empresa: Empresa
    ) -> str:
        """
        Obtiene el style_guide del cache o lo genera si es necesario.
        
        Flujo (igual que main.py):
        1. Verifica si hay cache válido en la tabla CacheEmpresa
        2. Si hay cache válido (hash coincide), retorna el style_guide SIN analizar
        3. Si NO hay cache válido:
           - Carga las imágenes de referencia desde R2
           - Analiza las referencias con Gemini
           - Guarda el style_guide y hash en CacheEmpresa
           - Retorna el style_guide
        
        Esto evita re-analizar las referencias cada vez que se genera un post.
        """
        # 1. Intentar obtener del cache
        cached = CacheService.get_cached_style_guide(db, empresa.id)
        if cached:
            print(f"📦 Usando style_guide en cache para empresa {empresa.nombre} (NO se analizan referencias)")
            return cached
        
        # 2. NO hay cache válido - necesitamos analizar
        print(f"🔍 Cache no encontrado o inválido. Analizando referencias para empresa {empresa.nombre}...")
        
        # 3. Cargar referencias de la base de datos
        referencias = db.query(ReferenciaEstilo).filter(
            ReferenciaEstilo.empresa_id == empresa.id
        ).all()
        
        if not referencias:
            print(f"⚠️ No hay referencias para empresa {empresa.nombre}")
            return ""
        
        # 4. Cargar imágenes de referencias desde R2
        # imagenes_urls es un JSON (lista de URLs)
        reference_images = []
        total_urls = 0
        for ref in referencias:
            if ref.imagenes_urls:  # Verificar que tenga URLs
                for url in ref.imagenes_urls:
                    total_urls += 1
                    img = self.image_service.load_image_from_url_sync(url)
                    if img:
                        reference_images.append(img)
                        if len(reference_images) >= self.config.max_references:
                            break
                if len(reference_images) >= self.config.max_references:
                    break
        
        print(f"   Cargadas {len(reference_images)} imágenes de {total_urls} URLs desde R2")
        
        if not reference_images:
            print(f"⚠️ No se pudieron cargar imágenes de referencia")
            return ""
        
        # 5. Analizar referencias con Gemini (esto es costoso, por eso usamos cache)
        print(f"🤖 Analizando {len(reference_images)} referencias con Gemini...")
        style_guide = self.analyzer.deep_analyze_references(reference_images)
        
        # 6. Guardar en cache (tabla CacheEmpresa)
        CacheService.save_style_guide(db, empresa.id, style_guide, referencias)
        print(f"✅ Style guide generado y guardado en cache (tabla cache_empresas)")
        
        return style_guide
    
    async def load_logo(self, empresa: Empresa) -> Optional[Image.Image]:
        """Carga el logo de la empresa"""
        if not empresa.logo_url:
            return None
        return self.image_service.load_image_from_url_sync(empresa.logo_url)
    
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
    
    def _pil_to_part(self, img: Image.Image) -> types.Part:
        """Convierte imagen PIL a Part de Gemini"""
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return types.Part.from_bytes(mime_type="image/png", data=buffer.getvalue())
    
    def _build_base_parts(
        self, 
        reference_images: List[Image.Image],
        logo_image: Optional[Image.Image],
        product_image: Optional[Image.Image] = None
    ) -> List[types.Part]:
        """Construye las partes base para la generación"""
        parts = []
        
        if reference_images:
            parts.append(types.Part.from_text(text=REFERENCES_INSTRUCTION))
            for ref_img in reference_images:
                parts.append(self._pil_to_part(ref_img))
        
        if logo_image:
            parts.append(types.Part.from_text(text=LOGO_INSTRUCTION))
            parts.append(self._pil_to_part(logo_image))
        
        if product_image:
            parts.append(types.Part.from_text(text=PRODUCT_INSTRUCTION))
            parts.append(self._pil_to_part(product_image))
        
        return parts
    
    def _build_multi_product_parts(
        self,
        reference_images: List[Image.Image],
        logo_image: Optional[Image.Image],
        product_images: List[Image.Image]
    ) -> List[types.Part]:
        """Construye las partes para múltiples productos"""
        parts = []
        
        if reference_images:
            parts.append(types.Part.from_text(text=REFERENCES_INSTRUCTION))
            for ref_img in reference_images:
                parts.append(self._pil_to_part(ref_img))
        
        if logo_image:
            parts.append(types.Part.from_text(text=LOGO_INSTRUCTION))
            parts.append(self._pil_to_part(logo_image))
        
        num_products = len(product_images)
        parts.append(types.Part.from_text(text=get_multi_product_instruction(num_products)))
        for i, prod_img in enumerate(product_images, 1):
            parts.append(types.Part.from_text(text=f"\n[PRODUCT {i}]"))
            parts.append(self._pil_to_part(prod_img))
        
        return parts
    
    async def _load_reference_images(self, db: Session, empresa_id: UUID) -> List[Image.Image]:
        """Carga las imágenes de referencia de una empresa"""
        referencias = db.query(ReferenciaEstilo).filter(
            ReferenciaEstilo.empresa_id == empresa_id
        ).limit(self.config.max_references).all()
        
        images = []
        for ref in referencias:
            if ref.imagenes_urls:  # Verificar que tenga URLs
                for url in ref.imagenes_urls:
                    img = self.image_service.load_image_from_url_sync(url)
                    if img:
                        images.append(img)
                        if len(images) >= self.config.max_references:
                            break
                if len(images) >= self.config.max_references:
                    break
        return images
    
    def _get_next_version_number(self, db: Session, post_id: UUID) -> int:
        """Obtiene el siguiente número de versión para un post"""
        max_version = db.query(VersionPost).filter(
            VersionPost.post_id == post_id
        ).order_by(VersionPost.numero_version.desc()).first()
        
        return (max_version.numero_version + 1) if max_version else 1
    
    # =========================================================================
    # CREAR POST CON PRODUCTO ÚNICO
    # =========================================================================
    
    async def create_post_with_product(
        self,
        db: Session,
        empresa: Empresa,
        user_id: UUID,
        request_usuario: str,
        imagen_producto: Image.Image,  # Cambiado: ahora recibe PIL Image directamente
        modo: ModoEstiloEnum = ModoEstiloEnum.CREATIVE,
        nombre_interno: Optional[str] = None,
        generar_ambas: bool = False,
        es_programado: bool = False,
        fecha_programada: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un post con un producto único.
        
        IMPORTANTE: La imagen del producto NO se guarda en R2 ni en la BD.
        Se usa temporalmente en memoria para generar el post.
        Solo se guardan las imágenes GENERADAS del post en R2.
        
        Args:
            db: Sesión de base de datos
            empresa: Empresa para la que se genera el post
            user_id: ID del usuario que crea el post
            request_usuario: Solicitud del usuario
            imagen_producto: PIL Image del producto (en memoria, no guardada)
            modo: CREATIVE o REFERENCE
            nombre_interno: Nombre interno opcional
            generar_ambas: Si True, genera ambas versiones
            es_programado: Si True, el post se programa para publicación futura
            fecha_programada: Fecha de programación (formato ISO string)
        """
        print(f"\n🎨 Creando post para {empresa.nombre}")
        
        if not imagen_producto:
            return {"status": "error", "mensaje": "No se pudo cargar la imagen del producto"}
        
        # 1. Obtener style_guide
        style_guide = await self.get_or_create_style_guide(db, empresa)
        
        # 2. Cargar imágenes de referencia y logo
        reference_images = await self._load_reference_images(db, empresa.id)
        logo_image = await self.load_logo(empresa)
        
        # La imagen del producto ya está en memoria, no necesitamos cargarla desde URL
        product_image = imagen_producto
        
        # 3. Crear el post en la base de datos
        # Parsear fecha_programada si está presente
        fecha_programada_dt = None
        if fecha_programada:
            try:
                fecha_programada_dt = datetime.fromisoformat(fecha_programada.replace('Z', '+00:00'))
            except Exception:
                fecha_programada_dt = None
        
        post = Post(
            empresa_id=empresa.id,
            creado_por=user_id,
            nombre_interno=nombre_interno,
            request_usuario=request_usuario,
            tipo_contenido=TipoContenido.SINGLE,
            modo_estilo=ModoEstilo(modo.value),
            es_programado=es_programado,
            fecha_programada=fecha_programada_dt,
            estado=EstadoPost.SCHEDULED if es_programado else EstadoPost.DRAFT
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        
        # 4. Análisis
        print("📊 Analizando...")
        user_intent = self.analyzer.analyze_user_intent(request_usuario, empresa)
        product_info = self.analyzer.analyze_product_basic(product_image)
        creative_context = ""
        if modo == ModoEstiloEnum.CREATIVE or generar_ambas:
            creative_context = self.analyzer.analyze_product_for_context(product_image)
        
        # 5. Construir partes base
        base_parts = self._build_base_parts(reference_images, logo_image, product_image)
        
        results = {}
        colors = ensure_colors_list(empresa.colores_marca, empresa.nombre)
        
        # 6. Generar versiones
        if generar_ambas:
            # Generar REFERENCE
            print("📋 Generando versión REFERENCE...")
            ref_prompt = get_reference_prompt(
                style_guide, empresa.nombre, ', '.join(colors),
                request_usuario, user_intent, product_info
            )
            ref_parts = base_parts + [types.Part.from_text(text=f"\n{ref_prompt}")]
            ref_img = self.gemini_client.generate_image(ref_parts)
            
            if ref_img:
                # Subir imagen a R2 en carpeta posts/
                filename = f"post_{post.id}_v1_reference.png"
                upload_result = upload_pil_image_to_r2(
                    ref_img,
                    folder="posts",
                    custom_filename=f"posts/{filename}",
                    format="PNG"
                )
                ref_url = upload_result["url"]
                
                version_ref = VersionPost(
                    post_id=post.id,
                    numero_version=1,
                    tipo_version=TipoVersion.ORIGINAL,
                    variante="reference",
                    imagen_url=ref_url
                )
                db.add(version_ref)
                results["reference"] = GenerationResult(
                    status="success",
                    version_id=version_ref.id,
                    imagen_url=ref_url,
                    modo="reference"
                )
            
            # Generar CREATIVE
            print("🎨 Generando versión CREATIVE...")
            creative_prompt = get_creative_prompt(
                style_guide, creative_context, empresa.nombre, colors,
                request_usuario, user_intent, product_info
            )
            creative_parts = base_parts + [types.Part.from_text(text=f"\n{creative_prompt}")]
            creative_img = self.gemini_client.generate_image(creative_parts)
            
            if creative_img:
                # Subir imagen a R2 en carpeta posts/
                filename = f"post_{post.id}_v1_creative.png"
                upload_result = upload_pil_image_to_r2(
                    creative_img,
                    folder="posts",
                    custom_filename=f"posts/{filename}",
                    format="PNG"
                )
                creative_url = upload_result["url"]
                
                version_creative = VersionPost(
                    post_id=post.id,
                    numero_version=1,
                    tipo_version=TipoVersion.ORIGINAL,
                    variante="creative",
                    imagen_url=creative_url
                )
                db.add(version_creative)
                results["creative"] = GenerationResult(
                    status="success",
                    version_id=version_creative.id,
                    imagen_url=creative_url,
                    modo="creative"
                )
        else:
            # Generar solo una versión
            if modo == ModoEstiloEnum.REFERENCE:
                prompt = get_reference_prompt(
                    style_guide, empresa.nombre, ', '.join(colors),
                    request_usuario, user_intent, product_info
                )
            else:
                prompt = get_creative_prompt(
                    style_guide, creative_context, empresa.nombre, colors,
                    request_usuario, user_intent, product_info
                )
            
            parts = base_parts + [types.Part.from_text(text=f"\n{prompt}")]
            generated = self.gemini_client.generate_image(parts)
            
            if generated:
                # Subir imagen a R2 en carpeta posts/
                filename = f"post_{post.id}_v1_{modo.value}.png"
                upload_result = upload_pil_image_to_r2(
                    generated,
                    folder="posts",
                    custom_filename=f"posts/{filename}",
                    format="PNG"
                )
                img_url = upload_result["url"]
                
                version = VersionPost(
                    post_id=post.id,
                    numero_version=1,
                    tipo_version=TipoVersion.ORIGINAL,
                    variante=modo.value,
                    imagen_url=img_url
                )
                db.add(version)
                results["generated"] = GenerationResult(
                    status="success",
                    version_id=version.id,
                    imagen_url=img_url,
                    modo=modo.value
                )
            else:
                results["generated"] = GenerationResult(
                    status="error",
                    mensaje="Falló la generación de la imagen"
                )
        
        db.commit()
        
        return {
            "status": "success",
            "post_id": post.id,
            "results": results
        }
    
    # =========================================================================
    # CREAR POST SCRATCH (SIN PRODUCTO)
    # =========================================================================
    
    async def create_scratch_post(
        self,
        db: Session,
        empresa: Empresa,
        user_id: UUID,
        request_usuario: str,
        nombre_interno: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un post desde cero sin imagen de producto.
        Ideal para anuncios, cierres, celebraciones, etc.
        """
        print(f"\n🎨 Creando post SCRATCH para {empresa.nombre}")
        
        # 1. Obtener style_guide
        style_guide = await self.get_or_create_style_guide(db, empresa)
        
        # 2. Cargar imágenes
        reference_images = await self._load_reference_images(db, empresa.id)
        logo_image = await self.load_logo(empresa)
        
        # 3. Crear el post en la base de datos
        post = Post(
            empresa_id=empresa.id,
            creado_por=user_id,
            nombre_interno=nombre_interno,
            request_usuario=request_usuario,
            tipo_contenido=TipoContenido.SCRATCH,
            modo_estilo=ModoEstilo.CREATIVE
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        
        # 4. Análisis
        print("📊 Analizando mensaje...")
        user_intent = self.analyzer.analyze_user_intent(request_usuario, empresa)
        message_analysis = self.analyzer.analyze_message_for_scratch(request_usuario, empresa)
        
        # 5. Construir prompt y partes
        colors = ensure_colors_list(empresa.colores_marca, empresa.nombre)
        prompt = get_scratch_prompt(
            style_guide, message_analysis, empresa.nombre, colors,
            request_usuario, user_intent
        )
        
        parts = self._build_base_parts(reference_images, logo_image)
        parts.append(types.Part.from_text(text=f"\n{prompt}"))
        
        # 6. Generar
        print("🚀 Generando imagen...")
        generated = self.gemini_client.generate_image(parts)
        
        if generated:
            # Subir imagen a R2 en carpeta posts/
            filename = f"post_{post.id}_v1_scratch.png"
            upload_result = upload_pil_image_to_r2(
                generated,
                folder="posts",
                custom_filename=f"posts/{filename}",
                format="PNG"
            )
            img_url = upload_result["url"]
            
            version = VersionPost(
                post_id=post.id,
                numero_version=1,
                tipo_version=TipoVersion.ORIGINAL,
                variante="scratch",
                imagen_url=img_url
            )
            db.add(version)
            db.commit()
            
            return {
                "status": "success",
                "post_id": post.id,
                "version_id": version.id,
                "imagen_url": img_url
            }
        
        return {"status": "error", "mensaje": "Falló la generación"}
    
    # =========================================================================
    # CREAR POST MULTI-PRODUCTO
    # =========================================================================
    
    async def create_multi_product_post(
        self,
        db: Session,
        empresa: Empresa,
        user_id: UUID,
        request_usuario: str,
        imagenes_productos: List[Image.Image],  # Cambiado: ahora recibe PIL Images directamente
        modo: ModoEstiloEnum = ModoEstiloEnum.CREATIVE,
        nombre_interno: Optional[str] = None,
        generar_ambas: bool = False,
        es_programado: bool = False,
        fecha_programada: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un post con múltiples productos (1-4).
        
        IMPORTANTE: Las imágenes de productos NO se guardan en R2 ni en la BD.
        Se usan temporalmente en memoria para generar el post.
        Solo se guardan las imágenes GENERADAS del post en R2.
        """
        num_products = len(imagenes_productos)
        if num_products < 1 or num_products > 4:
            return {"status": "error", "mensaje": "Se requieren entre 1 y 4 productos"}
        
        print(f"\n🎨 Creando post MULTI-PRODUCTO ({num_products}) para {empresa.nombre}")
        
        # 1. Obtener style_guide
        style_guide = await self.get_or_create_style_guide(db, empresa)
        
        # 2. Cargar imágenes de referencia y logo
        reference_images = await self._load_reference_images(db, empresa.id)
        logo_image = await self.load_logo(empresa)
        
        # Las imágenes de productos ya están en memoria, no necesitamos cargarlas desde URL
        product_images = imagenes_productos
        
        # 3. Crear el post en la base de datos
        # Parsear fecha_programada si está presente
        fecha_programada_dt = None
        if fecha_programada:
            try:
                fecha_programada_dt = datetime.fromisoformat(fecha_programada.replace('Z', '+00:00'))
            except Exception:
                fecha_programada_dt = None
        
        post = Post(
            empresa_id=empresa.id,
            creado_por=user_id,
            nombre_interno=nombre_interno,
            request_usuario=request_usuario,
            tipo_contenido=TipoContenido.MULTI,
            modo_estilo=ModoEstilo(modo.value),
            es_programado=es_programado,
            fecha_programada=fecha_programada_dt,
            estado=EstadoPost.SCHEDULED if es_programado else EstadoPost.DRAFT
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        
        # 4. Análisis
        print("📊 Analizando...")
        user_intent = self.analyzer.analyze_user_intent(request_usuario, empresa)
        products_info = self.analyzer.analyze_multiple_products(product_images)
        creative_context = ""
        if modo == ModoEstiloEnum.CREATIVE or generar_ambas:
            creative_context = self.analyzer.analyze_multiple_products_for_context(product_images)
        
        # 5. Construir partes base
        base_parts = self._build_multi_product_parts(reference_images, logo_image, product_images)
        
        results = {}
        colors = ensure_colors_list(empresa.colores_marca, empresa.nombre)
        num_products = len(product_images)
        
        # 6. Generar versiones
        if generar_ambas:
            # REFERENCE
            print("📋 Generando versión REFERENCE...")
            ref_prompt = get_multi_product_reference_prompt(
                style_guide, empresa.nombre, ', '.join(colors),
                request_usuario, user_intent, products_info, num_products
            )
            ref_parts = base_parts + [types.Part.from_text(text=f"\n{ref_prompt}")]
            ref_img = self.gemini_client.generate_image(ref_parts)
            
            if ref_img:
                # Subir imagen a R2 en carpeta posts/
                filename = f"post_{post.id}_v1_reference.png"
                upload_result = upload_pil_image_to_r2(
                    ref_img,
                    folder="posts",
                    custom_filename=f"posts/{filename}",
                    format="PNG"
                )
                ref_url = upload_result["url"]
                
                version_ref = VersionPost(
                    post_id=post.id,
                    numero_version=1,
                    tipo_version=TipoVersion.ORIGINAL,
                    variante="reference",
                    imagen_url=ref_url
                )
                db.add(version_ref)
                results["reference"] = GenerationResult(
                    status="success",
                    version_id=version_ref.id,
                    imagen_url=ref_url,
                    modo="reference"
                )
            
            # CREATIVE
            print("🎨 Generando versión CREATIVE...")
            creative_prompt = get_multi_product_creative_prompt(
                style_guide, creative_context, empresa.nombre, colors,
                request_usuario, user_intent, products_info, num_products
            )
            creative_parts = base_parts + [types.Part.from_text(text=f"\n{creative_prompt}")]
            creative_img = self.gemini_client.generate_image(creative_parts)
            
            if creative_img:
                # Subir imagen a R2 en carpeta posts/
                filename = f"post_{post.id}_v1_creative.png"
                upload_result = upload_pil_image_to_r2(
                    creative_img,
                    folder="posts",
                    custom_filename=f"posts/{filename}",
                    format="PNG"
                )
                creative_url = upload_result["url"]
                
                version_creative = VersionPost(
                    post_id=post.id,
                    numero_version=1,
                    tipo_version=TipoVersion.ORIGINAL,
                    variante="creative",
                    imagen_url=creative_url
                )
                db.add(version_creative)
                results["creative"] = GenerationResult(
                    status="success",
                    version_id=version_creative.id,
                    imagen_url=creative_url,
                    modo="creative"
                )
        else:
            # Solo una versión
            if modo == ModoEstiloEnum.REFERENCE:
                prompt = get_multi_product_reference_prompt(
                    style_guide, empresa.nombre, ', '.join(colors),
                    request_usuario, user_intent, products_info, num_products
                )
            else:
                prompt = get_multi_product_creative_prompt(
                    style_guide, creative_context, empresa.nombre, colors,
                    request_usuario, user_intent, products_info, num_products
                )
            
            parts = base_parts + [types.Part.from_text(text=f"\n{prompt}")]
            generated = self.gemini_client.generate_image(parts)
            
            if generated:
                # Subir imagen a R2 en carpeta posts/
                filename = f"post_{post.id}_v1_{modo.value}.png"
                upload_result = upload_pil_image_to_r2(
                    generated,
                    folder="posts",
                    custom_filename=f"posts/{filename}",
                    format="PNG"
                )
                img_url = upload_result["url"]
                
                version = VersionPost(
                    post_id=post.id,
                    numero_version=1,
                    tipo_version=TipoVersion.ORIGINAL,
                    variante=modo.value,
                    imagen_url=img_url
                )
                db.add(version)
                results["generated"] = GenerationResult(
                    status="success",
                    version_id=version.id,
                    imagen_url=img_url,
                    modo=modo.value
                )
        
        db.commit()
        
        return {
            "status": "success",
            "post_id": post.id,
            "num_products": num_products,
            "results": results
        }
    
    # =========================================================================
    # REGENERAR POST
    # =========================================================================
    
    async def regenerate_post(
        self,
        db: Session,
        post: Post,
        empresa: Empresa,
        feedback: str = "",
        version_base_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Regenera un post existente creando una versión completamente nueva.
        """
        print(f"\n🔄 Regenerando post {post.id}")
        
        # 1. Obtener versión base (la más reciente o la especificada)
        if version_base_id:
            version_base = db.query(VersionPost).filter(
                VersionPost.id == version_base_id,
                VersionPost.post_id == post.id
            ).first()
        else:
            version_base = db.query(VersionPost).filter(
                VersionPost.post_id == post.id
            ).order_by(VersionPost.numero_version.desc()).first()
        
        if not version_base or not version_base.imagen_url:
            return {"status": "error", "mensaje": "No se encontró versión para regenerar"}
        
        # 2. Cargar imagen del post existente
        existing_post_img = self.image_service.load_image_from_url_sync(version_base.imagen_url)
        if not existing_post_img:
            return {"status": "error", "mensaje": "No se pudo cargar la imagen del post existente"}
        
        # 3. Obtener style_guide y referencias
        style_guide = await self.get_or_create_style_guide(db, empresa)
        reference_images = await self._load_reference_images(db, empresa.id)
        logo_image = await self.load_logo(empresa)
        
        # 4. Analizar post existente
        print("📊 Analizando post existente...")
        post_analysis = self.analyzer.analyze_post_for_regeneration(existing_post_img)
        
        # 5. Construir prompt de regeneración
        colors = ensure_colors_list(empresa.colores_marca, empresa.nombre)
        prompt = get_regeneration_prompt(
            style_guide, post_analysis, empresa.nombre, colors, feedback
        )
        
        # 6. Construir partes (sin la imagen original para forzar cambios)
        parts = []
        if reference_images:
            parts.append(types.Part.from_text(text=REFERENCES_INSTRUCTION))
            for ref_img in reference_images:
                parts.append(self._pil_to_part(ref_img))
        
        parts.append(types.Part.from_text(text="""
══ IMPORTANT: CREATE A COMPLETELY DIFFERENT DESIGN ══
Do NOT recreate the same layout. The analysis below describes what TO CHANGE.
Use a DIFFERENT background, DIFFERENT layout structure, DIFFERENT visual approach.
"""))
        
        if logo_image:
            parts.append(types.Part.from_text(text=LOGO_INSTRUCTION))
            parts.append(self._pil_to_part(logo_image))
        
        parts.append(types.Part.from_text(text=f"\n{prompt}"))
        
        # 7. Generar
        print("🚀 Generando nueva versión...")
        generated = self.gemini_client.generate_image(parts)
        
        if generated:
            next_version = self._get_next_version_number(db, post.id)
            # Subir imagen a R2 en carpeta posts/
            filename = f"post_{post.id}_v{next_version}_regeneration.png"
            upload_result = upload_pil_image_to_r2(
                generated,
                folder="posts",
                custom_filename=f"posts/{filename}",
                format="PNG"
            )
            img_url = upload_result["url"]
            
            version = VersionPost(
                post_id=post.id,
                version_padre_id=version_base.id,
                numero_version=next_version,
                tipo_version=TipoVersion.REGENERACION,
                imagen_url=img_url,
                cambios_solicitados=feedback
            )
            db.add(version)
            db.commit()
            
            return {
                "status": "success",
                "post_id": post.id,
                "version_id": version.id,
                "numero_version": next_version,
                "imagen_url": img_url
            }
        
        return {"status": "error", "mensaje": "Falló la regeneración"}
    
    # =========================================================================
    # EDITAR POST
    # =========================================================================
    
    async def edit_post(
        self,
        db: Session,
        post: Post,
        empresa: Empresa,
        cambios: str,
        version_base_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Edita un post existente haciendo cambios específicos.
        A diferencia de regenerate, mantiene el diseño original.
        """
        print(f"\n✏️ Editando post {post.id}")
        
        # 1. Obtener versión base
        if version_base_id:
            version_base = db.query(VersionPost).filter(
                VersionPost.id == version_base_id,
                VersionPost.post_id == post.id
            ).first()
        else:
            version_base = db.query(VersionPost).filter(
                VersionPost.post_id == post.id
            ).order_by(VersionPost.numero_version.desc()).first()
        
        if not version_base or not version_base.imagen_url:
            return {"status": "error", "mensaje": "No se encontró versión para editar"}
        
        # 2. Cargar imagen del post existente
        existing_post_img = self.image_service.load_image_from_url_sync(version_base.imagen_url)
        if not existing_post_img:
            return {"status": "error", "mensaje": "No se pudo cargar la imagen del post existente"}
        
        # 3. Cargar referencias y logo
        reference_images = await self._load_reference_images(db, empresa.id)
        logo_image = await self.load_logo(empresa)
        
        # 4. Analizar solicitud de edición
        print("📊 Analizando cambios solicitados...")
        edit_analysis = self.analyzer.analyze_edit_request(cambios)
        
        # 5. Construir prompt de edición
        colors = ensure_colors_list(empresa.colores_marca, empresa.nombre)
        prompt = get_edit_post_prompt(edit_analysis, empresa.nombre, colors, cambios)
        
        # 6. Construir partes (incluyendo imagen original)
        parts = []
        parts.append(types.Part.from_text(text=POST_TO_EDIT_INSTRUCTION))
        parts.append(self._pil_to_part(existing_post_img))
        
        if reference_images:
            parts.append(types.Part.from_text(text="""
══ STYLE REFERENCES (for consistency) ══
These show the brand style. Use them only to maintain visual consistency 
with the brand, NOT to change the design. Keep the edited post's style similar to the original.
"""))
            for ref_img in reference_images[:3]:
                parts.append(self._pil_to_part(ref_img))
        
        if logo_image:
            parts.append(types.Part.from_text(text="""
══ COMPANY LOGO (use if repositioning is needed) ══
This is the company logo. Use it ONLY if the edit requires moving or resizing the logo.
"""))
            parts.append(self._pil_to_part(logo_image))
        
        parts.append(types.Part.from_text(text=f"\n{prompt}"))
        
        # 7. Generar
        print("🚀 Aplicando cambios...")
        generated = self.gemini_client.generate_image(parts)
        
        if generated:
            next_version = self._get_next_version_number(db, post.id)
            # Subir imagen a R2 en carpeta posts/
            filename = f"post_{post.id}_v{next_version}_edit.png"
            upload_result = upload_pil_image_to_r2(
                generated,
                folder="posts",
                custom_filename=f"posts/{filename}",
                format="PNG"
            )
            img_url = upload_result["url"]
            
            version = VersionPost(
                post_id=post.id,
                version_padre_id=version_base.id,
                numero_version=next_version,
                tipo_version=TipoVersion.EDICION,
                imagen_url=img_url,
                cambios_solicitados=cambios
            )
            db.add(version)
            db.commit()
            
            return {
                "status": "success",
                "post_id": post.id,
                "version_id": version.id,
                "numero_version": next_version,
                "imagen_url": img_url,
                "cambios_aplicados": cambios
            }
        
        return {"status": "error", "mensaje": "Falló la edición"}
    
    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================
    
    def get_post_with_versions(self, db: Session, post_id: UUID) -> Optional[Post]:
        """Obtiene un post con todas sus versiones"""
        return db.query(Post).filter(Post.id == post_id).first()
    
    def get_empresa_posts(
        self, 
        db: Session, 
        empresa_id: UUID, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Post]:
        """Obtiene los posts de una empresa"""
        return db.query(Post).filter(
            Post.empresa_id == empresa_id
        ).order_by(Post.creado_en.desc()).offset(skip).limit(limit).all()
    
    def count_empresa_posts(self, db: Session, empresa_id: UUID) -> int:
        """Cuenta el total de posts de una empresa"""
        return db.query(Post).filter(Post.empresa_id == empresa_id).count()
    
    def select_version(self, db: Session, post: Post, version_id: UUID) -> bool:
        """Selecciona una versión como la elegida para el post"""
        version = db.query(VersionPost).filter(
            VersionPost.id == version_id,
            VersionPost.post_id == post.id
        ).first()
        
        if not version:
            return False
        
        post.version_elegida_id = version_id
        db.commit()
        return True
    
    def update_post_estado(self, db: Session, post: Post, nuevo_estado: EstadoPost):
        """Actualiza el estado de un post"""
        post.estado = nuevo_estado
        db.commit()


# Instancia global del servicio
post_service = PostService()

