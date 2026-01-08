"""
Servicio de Generación de Posts de Instagram
Contiene toda la lógica de generación conectada a la base de datos.
"""

import asyncio
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from PIL import Image
from sqlalchemy.orm import Session
from google.genai import types

# Modelos y DTOs
from Models import (
    Empresa, 
    ReferenciaEstilo, 
    Post, 
    VersionPost,
    TipoContenido,
    ModoEstilo,
    EstadoPost,
    TipoVersion
)
from Dto.PostDto import (
    ModoEstiloEnum,
    GenerationResult
)

# Servicios
from Services.config_service import SystemConfig
from Services.gemini_service import GeminiService
from Services.image_service import ImageService
from Services.cache_service import CacheService
from Services.analyzer_service import AnalyzerService
from Utils.color_utils import ensure_colors_list
from Utils.r2_storage import upload_pil_image_to_r2

# Importar prompts desde el proyecto raíz
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from prompts import (
    REFERENCES_INSTRUCTION,
    LOGO_INSTRUCTION,
    PRODUCT_INSTRUCTION,
    POST_TO_EDIT_INSTRUCTION,
    get_reference_prompt,
    get_creative_prompt,
    get_scratch_prompt,
    get_regeneration_prompt,
    get_multi_product_reference_prompt,
    get_multi_product_creative_prompt,
    get_multi_product_instruction,
    get_edit_post_prompt,
)


class PostService:
    """Servicio principal para generación y gestión de posts"""
    
    def __init__(self):
        self.config = SystemConfig()
        self.gemini_service = GeminiService(self.config)
        self.analyzer = AnalyzerService(self.gemini_service)
        self.image_service = ImageService()
    
    # =========================================================================
    # MÉTODOS DE INICIALIZACIÓN
    # =========================================================================
    
    async def get_or_create_style_guide(self, db: Session, empresa: Empresa) -> str:
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
        
        # 4. Cargar imágenes de referencias desde R2 (operaciones bloqueantes en hilos)
        reference_images = []
        total_urls = 0
        for ref in referencias:
            if ref.imagenes_urls:
                for url in ref.imagenes_urls:
                    total_urls += 1
                    # ✅ Ejecutar en hilo para no bloquear el event loop
                    img = await asyncio.to_thread(self.image_service.load_image_from_url_sync, url)
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
        
        # 5. Analizar referencias con Gemini (operación MUY bloqueante - en hilo)
        print(f"🤖 Analizando {len(reference_images)} referencias con Gemini...")
        style_guide = await asyncio.to_thread(self.analyzer.deep_analyze_references, reference_images)
        
        # 6. Guardar en cache (tabla CacheEmpresa)
        CacheService.save_style_guide(db, empresa.id, style_guide, referencias)
        print(f"✅ Style guide generado y guardado en cache (tabla cache_empresas)")
        
        return style_guide
    
    async def load_logo(self, empresa: Empresa) -> Optional[Image.Image]:
        """Carga el logo de la empresa"""
        if not empresa.logo_url:
            return None
        # ✅ Ejecutar en hilo para no bloquear el event loop
        return await asyncio.to_thread(self.image_service.load_image_from_url_sync, empresa.logo_url)
    
    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
    
    def _pil_to_part(self, img: Image.Image) -> types.Part:
        """Convierte imagen PIL a Part de Gemini"""
        return self.gemini_service.pil_to_part(img)
    
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
            if ref.imagenes_urls:
                for url in ref.imagenes_urls:
                    # ✅ Ejecutar en hilo para no bloquear el event loop
                    img = await asyncio.to_thread(self.image_service.load_image_from_url_sync, url)
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
        imagen_producto: Image.Image,
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
        """
        print(f"\n🎨 Creando post para {empresa.nombre}")
        
        if not imagen_producto:
            return {"status": "error", "mensaje": "No se pudo cargar la imagen del producto"}
        
        # 1. Obtener style_guide
        style_guide = await self.get_or_create_style_guide(db, empresa)
        
        # 2. Cargar imágenes de referencia y logo
        reference_images = await self._load_reference_images(db, empresa.id)
        logo_image = await self.load_logo(empresa)
        product_image = imagen_producto
        
        # 3. Crear el post en la base de datos
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
        db.commit()  # ✅ Commit temprano - libera la transacción
        db.refresh(post)
        post_id = post.id  # Guardar ID para usar después
        
        # ✅ TRANSACCIÓN CERRADA - Las siguientes operaciones NO necesitan DB abierta
        # Esto permite que otros requests usen la DB mientras procesamos
        
        # 4. Análisis (operaciones largas bloqueantes - ejecutar en hilos)
        print("📊 Analizando...")
        # ✅ Ejecutar análisis en paralelo cuando sea posible
        if modo == ModoEstiloEnum.CREATIVE or generar_ambas:
            # Ejecutar user_intent y product_basic en paralelo, luego creative_context
            user_intent, product_info = await asyncio.gather(
                asyncio.to_thread(self.analyzer.analyze_user_intent, request_usuario, empresa),
                asyncio.to_thread(self.analyzer.analyze_product_basic, product_image)
            )
            creative_context = await asyncio.to_thread(
                self.analyzer.analyze_product_for_context, product_image
            )
        else:
            # Solo necesitamos user_intent y product_basic
            user_intent, product_info = await asyncio.gather(
                asyncio.to_thread(self.analyzer.analyze_user_intent, request_usuario, empresa),
                asyncio.to_thread(self.analyzer.analyze_product_basic, product_image)
            )
            creative_context = ""
        
        # 5. Construir partes base
        base_parts = self._build_base_parts(reference_images, logo_image, product_image)
        
        results = {}
        colors = ensure_colors_list(empresa.colores_marca, empresa.nombre)
        
        # 6. Generar versiones (operaciones MUY largas - NO necesitan DB)
        if generar_ambas:
            # Generar REFERENCE
            print("📋 Generando versión REFERENCE...")
            ref_prompt = get_reference_prompt(
                style_guide, empresa.nombre, ', '.join(colors),
                request_usuario, user_intent, product_info
            )
            ref_parts = base_parts + [types.Part.from_text(text=f"\n{ref_prompt}")]
            # ✅ Ejecutar generación en hilo para no bloquear el event loop
            ref_img = await asyncio.to_thread(self.gemini_service.generate_image, ref_parts)
            
            if ref_img:
                filename = f"post_{post_id}_v1_reference.png"
                upload_result = upload_pil_image_to_r2(
                    ref_img, folder="posts", custom_filename=f"posts/{filename}", format="PNG"
                )
                ref_url = upload_result["url"]
                
                # ✅ ABRIR TRANSACCIÓN SOLO PARA GUARDAR
                version_ref = VersionPost(
                    post_id=post_id, numero_version=1, tipo_version=TipoVersion.ORIGINAL,
                    variante="reference", imagen_url=ref_url
                )
                db.add(version_ref)
                db.commit()  # ✅ Commit inmediato - libera transacción
                results["reference"] = GenerationResult(
                    status="success", version_id=version_ref.id,
                    imagen_url=ref_url, modo="reference"
                )
            
            # Generar CREATIVE
            print("🎨 Generando versión CREATIVE...")
            creative_prompt = get_creative_prompt(
                style_guide, creative_context, empresa.nombre, colors,
                request_usuario, user_intent, product_info
            )
            creative_parts = base_parts + [types.Part.from_text(text=f"\n{creative_prompt}")]
            # ✅ Ejecutar generación en hilo para no bloquear el event loop
            creative_img = await asyncio.to_thread(self.gemini_service.generate_image, creative_parts)
            
            if creative_img:
                filename = f"post_{post_id}_v1_creative.png"
                upload_result = upload_pil_image_to_r2(
                    creative_img, folder="posts", custom_filename=f"posts/{filename}", format="PNG"
                )
                creative_url = upload_result["url"]
                
                # ✅ ABRIR TRANSACCIÓN SOLO PARA GUARDAR
                version_creative = VersionPost(
                    post_id=post_id, numero_version=1, tipo_version=TipoVersion.ORIGINAL,
                    variante="creative", imagen_url=creative_url
                )
                db.add(version_creative)
                db.commit()  # ✅ Commit inmediato - libera transacción
                results["creative"] = GenerationResult(
                    status="success", version_id=version_creative.id,
                    imagen_url=creative_url, modo="creative"
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
            # ✅ Ejecutar generación en hilo para no bloquear el event loop
            generated = await asyncio.to_thread(self.gemini_service.generate_image, parts)
            
            if generated:
                filename = f"post_{post_id}_v1_{modo.value}.png"
                upload_result = upload_pil_image_to_r2(
                    generated, folder="posts", custom_filename=f"posts/{filename}", format="PNG"
                )
                img_url = upload_result["url"]
                
                # ✅ ABRIR TRANSACCIÓN SOLO PARA GUARDAR
                version = VersionPost(
                    post_id=post_id, numero_version=1, tipo_version=TipoVersion.ORIGINAL,
                    variante=modo.value, imagen_url=img_url
                )
                db.add(version)
                db.commit()  # ✅ Commit inmediato - libera transacción
                results["generated"] = GenerationResult(
                    status="success", version_id=version.id,
                    imagen_url=img_url, modo=modo.value
                )
            else:
                results["generated"] = GenerationResult(
                    status="error", mensaje="Falló la generación de la imagen"
                )
        
        return {
            "status": "success",
            "post_id": post_id,
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
        """Crea un post desde cero sin imagen de producto"""
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
        db.commit()  # ✅ Commit temprano - libera la transacción
        db.refresh(post)
        post_id = post.id  # Guardar ID para usar después
        
        # ✅ TRANSACCIÓN CERRADA - Las siguientes operaciones NO necesitan DB abierta
        
        # 4. Análisis (operaciones largas bloqueantes - ejecutar en hilos en paralelo)
        print("📊 Analizando mensaje...")
        # ✅ Ejecutar ambos análisis en paralelo para mayor velocidad
        user_intent, message_analysis = await asyncio.gather(
            asyncio.to_thread(self.analyzer.analyze_user_intent, request_usuario, empresa),
            asyncio.to_thread(self.analyzer.analyze_message_for_scratch, request_usuario, empresa)
        )
        
        # 5. Construir prompt y partes
        colors = ensure_colors_list(empresa.colores_marca, empresa.nombre)
        prompt = get_scratch_prompt(
            style_guide, message_analysis, empresa.nombre, colors,
            request_usuario, user_intent
        )
        
        parts = self._build_base_parts(reference_images, logo_image)
        parts.append(types.Part.from_text(text=f"\n{prompt}"))
        
        # 6. Generar (operación MUY larga bloqueante - ejecutar en hilo)
        print("🚀 Generando imagen...")
        # ✅ Ejecutar generación en hilo para no bloquear el event loop
        generated = await asyncio.to_thread(self.gemini_service.generate_image, parts)
        
        if generated:
            filename = f"post_{post_id}_v1_scratch.png"
            upload_result = upload_pil_image_to_r2(
                generated, folder="posts", custom_filename=f"posts/{filename}", format="PNG"
            )
            img_url = upload_result["url"]
            
            # ✅ ABRIR TRANSACCIÓN SOLO PARA GUARDAR
            version = VersionPost(
                post_id=post_id, numero_version=1, tipo_version=TipoVersion.ORIGINAL,
                variante="scratch", imagen_url=img_url
            )
            db.add(version)
            db.commit()  # ✅ Commit inmediato - libera transacción
            
            return {
                "status": "success",
                "post_id": post_id,
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
        imagenes_productos: List[Image.Image],
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
        product_images = imagenes_productos
        
        # 3. Crear el post en la base de datos
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
        db.commit()  # ✅ Commit temprano - libera la transacción
        db.refresh(post)
        post_id = post.id  # Guardar ID para usar después
        
        # ✅ TRANSACCIÓN CERRADA - Las siguientes operaciones NO necesitan DB abierta
        
        # 4. Análisis (operaciones largas bloqueantes - ejecutar en hilos)
        print("📊 Analizando...")
        # ✅ Ejecutar análisis en paralelo cuando sea posible
        if modo == ModoEstiloEnum.CREATIVE or generar_ambas:
            # Ejecutar user_intent y products_info en paralelo, luego creative_context
            user_intent, products_info = await asyncio.gather(
                asyncio.to_thread(self.analyzer.analyze_user_intent, request_usuario, empresa),
                asyncio.to_thread(self.analyzer.analyze_multiple_products, product_images)
            )
            creative_context = await asyncio.to_thread(
                self.analyzer.analyze_multiple_products_for_context, product_images
            )
        else:
            # Solo necesitamos user_intent y products_info
            user_intent, products_info = await asyncio.gather(
                asyncio.to_thread(self.analyzer.analyze_user_intent, request_usuario, empresa),
                asyncio.to_thread(self.analyzer.analyze_multiple_products, product_images)
            )
            creative_context = ""
        
        # 5. Construir partes base
        base_parts = self._build_multi_product_parts(reference_images, logo_image, product_images)
        
        results = {}
        colors = ensure_colors_list(empresa.colores_marca, empresa.nombre)
        num_products = len(product_images)
        
        # 6. Generar versiones (operaciones MUY largas - NO necesitan DB)
        if generar_ambas:
            # REFERENCE
            print("📋 Generando versión REFERENCE...")
            ref_prompt = get_multi_product_reference_prompt(
                style_guide, empresa.nombre, ', '.join(colors),
                request_usuario, user_intent, products_info, num_products
            )
            ref_parts = base_parts + [types.Part.from_text(text=f"\n{ref_prompt}")]
            # ✅ Ejecutar generación en hilo para no bloquear el event loop
            ref_img = await asyncio.to_thread(self.gemini_service.generate_image, ref_parts)
            
            if ref_img:
                filename = f"post_{post_id}_v1_reference.png"
                upload_result = upload_pil_image_to_r2(
                    ref_img, folder="posts", custom_filename=f"posts/{filename}", format="PNG"
                )
                ref_url = upload_result["url"]
                
                # ✅ ABRIR TRANSACCIÓN SOLO PARA GUARDAR
                version_ref = VersionPost(
                    post_id=post_id, numero_version=1, tipo_version=TipoVersion.ORIGINAL,
                    variante="reference", imagen_url=ref_url
                )
                db.add(version_ref)
                db.commit()  # ✅ Commit inmediato - libera transacción
                results["reference"] = GenerationResult(
                    status="success", version_id=version_ref.id,
                    imagen_url=ref_url, modo="reference"
                )
            
            # CREATIVE
            print("🎨 Generando versión CREATIVE...")
            creative_prompt = get_multi_product_creative_prompt(
                style_guide, creative_context, empresa.nombre, colors,
                request_usuario, user_intent, products_info, num_products
            )
            creative_parts = base_parts + [types.Part.from_text(text=f"\n{creative_prompt}")]
            # ✅ Ejecutar generación en hilo para no bloquear el event loop
            creative_img = await asyncio.to_thread(self.gemini_service.generate_image, creative_parts)
            
            if creative_img:
                filename = f"post_{post_id}_v1_creative.png"
                upload_result = upload_pil_image_to_r2(
                    creative_img, folder="posts", custom_filename=f"posts/{filename}", format="PNG"
                )
                creative_url = upload_result["url"]
                
                # ✅ ABRIR TRANSACCIÓN SOLO PARA GUARDAR
                version_creative = VersionPost(
                    post_id=post_id, numero_version=1, tipo_version=TipoVersion.ORIGINAL,
                    variante="creative", imagen_url=creative_url
                )
                db.add(version_creative)
                db.commit()  # ✅ Commit inmediato - libera transacción
                results["creative"] = GenerationResult(
                    status="success", version_id=version_creative.id,
                    imagen_url=creative_url, modo="creative"
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
            # ✅ Ejecutar generación en hilo para no bloquear el event loop
            generated = await asyncio.to_thread(self.gemini_service.generate_image, parts)
            
            if generated:
                filename = f"post_{post_id}_v1_{modo.value}.png"
                upload_result = upload_pil_image_to_r2(
                    generated, folder="posts", custom_filename=f"posts/{filename}", format="PNG"
                )
                img_url = upload_result["url"]
                
                # ✅ ABRIR TRANSACCIÓN SOLO PARA GUARDAR
                version = VersionPost(
                    post_id=post_id, numero_version=1, tipo_version=TipoVersion.ORIGINAL,
                    variante=modo.value, imagen_url=img_url
                )
                db.add(version)
                db.commit()  # ✅ Commit inmediato - libera transacción
                results["generated"] = GenerationResult(
                    status="success", version_id=version.id,
                    imagen_url=img_url, modo=modo.value
                )
        
        return {
            "status": "success",
            "post_id": post_id,
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
        """Regenera un post existente creando una versión completamente nueva"""
        print(f"\n🔄 Regenerando post {post.id}")
        
        # 1. Obtener versión base (operación rápida)
        if version_base_id:
            version_base = db.query(VersionPost).filter(
                VersionPost.id == version_base_id, VersionPost.post_id == post.id
            ).first()
        else:
            version_base = db.query(VersionPost).filter(
                VersionPost.post_id == post.id
            ).order_by(VersionPost.numero_version.desc()).first()
        
        if not version_base or not version_base.imagen_url:
            return {"status": "error", "mensaje": "No se encontró versión para regenerar"}
        
        # Guardar datos necesarios antes de cerrar transacción
        post_id = post.id
        version_base_id_saved = version_base.id
        imagen_url_base = version_base.imagen_url
        next_version = self._get_next_version_number(db, post.id)
        
        # ✅ CERRAR TRANSACCIÓN - Las siguientes operaciones NO necesitan DB abierta
        
        # 2. Cargar imagen del post existente (operación bloqueante - ejecutar en hilo)
        existing_post_img = await asyncio.to_thread(
            self.image_service.load_image_from_url_sync, imagen_url_base
        )
        if not existing_post_img:
            return {"status": "error", "mensaje": "No se pudo cargar la imagen del post existente"}
        
        # 3. Obtener style_guide y referencias (necesita DB, pero es rápido)
        style_guide = await self.get_or_create_style_guide(db, empresa)
        reference_images = await self._load_reference_images(db, empresa.id)
        logo_image = await self.load_logo(empresa)
        
        # ✅ CERRAR TRANSACCIÓN - Las siguientes operaciones NO necesitan DB abierta
        
        # 4. Analizar post existente (operación larga bloqueante - ejecutar en hilo)
        print("📊 Analizando post existente...")
        post_analysis = await asyncio.to_thread(
            self.analyzer.analyze_post_for_regeneration, existing_post_img
        )
        
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
        
        # 7. Generar (operación MUY larga bloqueante - ejecutar en hilo)
        print("🚀 Generando nueva versión...")
        # ✅ Ejecutar generación en hilo para no bloquear el event loop
        generated = await asyncio.to_thread(self.gemini_service.generate_image, parts)
        
        if generated:
            filename = f"post_{post_id}_v{next_version}_regeneration.png"
            upload_result = upload_pil_image_to_r2(
                generated, folder="posts", custom_filename=f"posts/{filename}", format="PNG"
            )
            img_url = upload_result["url"]
            
            # ✅ ABRIR TRANSACCIÓN SOLO PARA GUARDAR
            version = VersionPost(
                post_id=post_id, version_padre_id=version_base_id_saved,
                numero_version=next_version, tipo_version=TipoVersion.REGENERATION,
                imagen_url=img_url, cambios_solicitados=feedback
            )
            db.add(version)
            db.commit()  # ✅ Commit inmediato - libera transacción
            
            return {
                "status": "success",
                "post_id": post_id,
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
        """Edita un post existente haciendo cambios específicos"""
        print(f"\n✏️ Editando post {post.id}")
        
        # 1. Obtener versión base (operación rápida)
        if version_base_id:
            # Si se especifica una versión, usar esa específica
            version_base = db.query(VersionPost).filter(
                VersionPost.id == version_base_id, VersionPost.post_id == post.id
            ).first()
        else:
            # ✅ Buscar la última versión EDIT primero
            # Si no hay ninguna EDIT, entonces usar la última versión en general
            version_base = db.query(VersionPost).filter(
                VersionPost.post_id == post.id,
                VersionPost.tipo_version == TipoVersion.EDIT  # Buscar solo versiones EDIT
            ).order_by(VersionPost.numero_version.desc()).first()
            
            # Si no hay ninguna versión EDIT, usar la última versión en general
            if not version_base:
                version_base = db.query(VersionPost).filter(
                    VersionPost.post_id == post.id
                ).order_by(VersionPost.numero_version.desc()).first()
        
        if not version_base or not version_base.imagen_url:
            return {"status": "error", "mensaje": "No se encontró versión para editar"}
        
        # Guardar datos necesarios antes de cerrar transacción
        post_id = post.id
        version_base_id_saved = version_base.id
        imagen_url_base = version_base.imagen_url
        next_version = self._get_next_version_number(db, post.id)
        
        # ✅ CERRAR TRANSACCIÓN - Las siguientes operaciones NO necesitan DB abierta
        
        # 2. Cargar imagen del post existente (operación bloqueante - ejecutar en hilo)
        existing_post_img = await asyncio.to_thread(
            self.image_service.load_image_from_url_sync, imagen_url_base
        )
        if not existing_post_img:
            return {"status": "error", "mensaje": "No se pudo cargar la imagen del post existente"}
        
        # 3. Cargar referencias y logo (necesita DB, pero es rápido)
        reference_images = await self._load_reference_images(db, empresa.id)
        logo_image = await self.load_logo(empresa)
        
        # ✅ CERRAR TRANSACCIÓN - Las siguientes operaciones NO necesitan DB abierta
        
        # 4. Analizar solicitud de edición (operación larga bloqueante - ejecutar en hilo)
        print("📊 Analizando cambios solicitados...")
        edit_analysis = await asyncio.to_thread(self.analyzer.analyze_edit_request, cambios)
        
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
        
        # 7. Generar (operación MUY larga bloqueante - ejecutar en hilo)
        print("🚀 Aplicando cambios...")
        # ✅ Ejecutar generación en hilo para no bloquear el event loop
        generated = await asyncio.to_thread(self.gemini_service.generate_image, parts)
        
        if generated:
            filename = f"post_{post_id}_v{next_version}_edit.png"
            upload_result = upload_pil_image_to_r2(
                generated, folder="posts", custom_filename=f"posts/{filename}", format="PNG"
            )
            img_url = upload_result["url"]
            
            # ✅ ABRIR TRANSACCIÓN SOLO PARA GUARDAR
            version = VersionPost(
                post_id=post_id, version_padre_id=version_base_id_saved,
                numero_version=next_version, tipo_version=TipoVersion.EDIT,
                imagen_url=img_url, cambios_solicitados=cambios
            )
            db.add(version)
            db.commit()  # ✅ Commit inmediato - libera transacción
            
            return {
                "status": "success",
                "post_id": post_id,
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
            VersionPost.id == version_id, VersionPost.post_id == post.id
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
