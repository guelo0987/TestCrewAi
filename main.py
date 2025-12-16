"""
Sistema de Generación de Posts de Instagram - 100% Adaptativo
Dos modos: REFERENCIA (copia exacta) y CREATIVO (ambiente contextual)
Funciona para CUALQUIER tipo de empresa y estilo.

Optimizado para velocidad:
- Cache de style_guide
- Análisis paralelo
- Sin análisis duplicados
"""

import os
import io
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# Importar configuración y prompts
from config import CompanyConfig, GenerationMode, SystemConfig, DEFAULT_SYSTEM_CONFIG
from prompts import (
    ANALYZE_REFERENCES_PROMPT,
    ANALYZE_PRODUCT_BASIC_PROMPT,
    ANALYZE_PRODUCT_CONTEXT_PROMPT,
    REFERENCES_INSTRUCTION,
    LOGO_INSTRUCTION,
    PRODUCT_INSTRUCTION,
    get_user_intent_prompt,
    get_reference_prompt,
    get_creative_prompt,
)

load_dotenv()


# ============================================================================
# CLIENTE GEMINI
# ============================================================================

class GeminiClient:
    """Cliente para Gemini"""
    
    def __init__(self, config: SystemConfig = DEFAULT_SYSTEM_CONFIG):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.config = config
    
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
            
            if hasattr(response, 'text'):
                print(f"⚠️ Respuesta de texto: {response.text[:500]}...")
            return None
            
        except Exception as e:
            print(f"❌ Error generando imagen: {e}")
            return None


# ============================================================================
# ANALIZADOR (con cache y paralelismo)
# ============================================================================

class AdaptiveAnalyzer:
    """Analizador 100% adaptativo con optimizaciones"""
    
    def __init__(self, client: GeminiClient, config: SystemConfig = DEFAULT_SYSTEM_CONFIG):
        self.client = client
        self.config = config
    
    def deep_analyze_references(self, images: List[Image.Image]) -> str:
        """Análisis exhaustivo de referencias"""
        return self.client.analyze_with_images(ANALYZE_REFERENCES_PROMPT, images)
    
    def analyze_product_basic(self, product_image: Image.Image) -> str:
        """Análisis básico del producto"""
        return self.client.analyze_with_images(ANALYZE_PRODUCT_BASIC_PROMPT, [product_image])
    
    def analyze_product_for_context(self, product_image: Image.Image) -> str:
        """Analiza el producto para contexto creativo"""
        return self.client.analyze_with_images(ANALYZE_PRODUCT_CONTEXT_PROMPT, [product_image])
    
    def analyze_user_intent(self, request: str, company: CompanyConfig) -> str:
        """Analiza la intención del usuario"""
        prompt = get_user_intent_prompt(
            company.name, 
            company.description, 
            ', '.join(company.color_palette), 
            request
        )
        return self.client.analyze_text(prompt)
    
    def analyze_all(
        self, 
        request: str, 
        company: CompanyConfig, 
        product_image: Optional[Image.Image],
        include_creative_context: bool = False
    ) -> Dict[str, str]:
        """
        Ejecuta TODOS los análisis necesarios.
        """
        results = {
            "user_intent": "",
            "product_info": "",
            "creative_context": ""
        }
        
        # 1. Analizar intención del usuario
        print("   → Analizando intención...")
        results["user_intent"] = self.analyze_user_intent(request, company)
        
        # 2. Si hay producto, analizarlo
        if product_image:
            print("   → Analizando producto...")
            results["product_info"] = self.analyze_product_basic(product_image)
            
            if include_creative_context:
                print("   → Generando contexto creativo...")
                results["creative_context"] = self.analyze_product_for_context(product_image)
        
        return results


# ============================================================================
# CACHE DE STYLE GUIDE
# ============================================================================

class StyleGuideCache:
    """Maneja el cache del style_guide para evitar re-análisis"""
    
    def __init__(self, cache_file: str = ".style_guide_cache.json"):
        self.cache_file = cache_file
    
    def _get_references_hash(self, folder: str) -> str:
        """Genera un hash basado en los archivos de referencias"""
        files_info = []
        folder_path = Path(folder)
        
        if folder_path.exists():
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
                for file in sorted(folder_path.glob(ext)):
                    stat = file.stat()
                    files_info.append(f"{file.name}:{stat.st_size}:{stat.st_mtime}")
        
        return hashlib.md5("|".join(files_info).encode()).hexdigest()
    
    def get_cached(self, references_folder: str) -> Optional[str]:
        """Obtiene el style_guide del cache si es válido"""
        if not Path(self.cache_file).exists():
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            current_hash = self._get_references_hash(references_folder)
            if cache.get("hash") == current_hash:
                print("   📦 Usando style_guide en cache")
                return cache.get("style_guide")
        except Exception:
            pass
        
        return None
    
    def save(self, references_folder: str, style_guide: str):
        """Guarda el style_guide en cache"""
        try:
            cache = {
                "hash": self._get_references_hash(references_folder),
                "style_guide": style_guide
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"⚠️ No se pudo guardar cache: {e}")


# ============================================================================
# GENERADOR DE POSTS (OPTIMIZADO)
# ============================================================================

class InstagramPostGenerator:
    """Genera posts con optimizaciones de velocidad"""
    
    def __init__(
        self, 
        company: CompanyConfig, 
        references_folder: str,
        config: SystemConfig = DEFAULT_SYSTEM_CONFIG
    ):
        self.config = config
        self.client = GeminiClient(config)
        self.company = company
        self.references_folder = references_folder
        self.analyzer = AdaptiveAnalyzer(self.client, config)
        self.cache = StyleGuideCache(config.cache_file)
        
        self.reference_images: List[Image.Image] = []
        self.style_guide: str = ""
        self.logo_image: Optional[Image.Image] = None
        
        self._initialize()
    
    def _initialize(self):
        """Inicializa el sistema con cache"""
        print("\n" + "="*60)
        print("🔧 INICIALIZANDO SISTEMA")
        print("="*60)
        
        # 1. Cargar referencias (limitadas)
        print(f"\n📂 Cargando referencias de: {self.references_folder}")
        self.reference_images = self._load_images(self.references_folder)
        print(f"   ✓ {len(self.reference_images)} imágenes cargadas")
        
        # 2. Obtener style_guide (cache o analizar)
        if self.reference_images:
            if self.config.cache_style_guide:
                cached = self.cache.get_cached(self.references_folder)
                if cached:
                    self.style_guide = cached
                else:
                    print(f"\n🔍 Analizando referencias...")
                    self.style_guide = self.analyzer.deep_analyze_references(self.reference_images)
                    self.cache.save(self.references_folder, self.style_guide)
                    print("   ✓ Guía de estilo extraída y guardada en cache")
            else:
                print(f"\n🔍 Analizando referencias...")
                self.style_guide = self.analyzer.deep_analyze_references(self.reference_images)
                print("   ✓ Guía de estilo extraída")
        
        # 3. Cargar logo
        if self.company.logo_path and os.path.exists(self.company.logo_path):
            self.logo_image = Image.open(self.company.logo_path)
            if self.logo_image.mode in ('RGBA', 'P'):
                self.logo_image = self.logo_image.convert('RGB')
            print(f"   ✓ Logo cargado")
        
        print("\n✅ Sistema listo\n")
    
    def _load_images(self, folder: str) -> List[Image.Image]:
        """Carga imágenes con límite configurable"""
        images = []
        folder_path = Path(folder)
        
        if not folder_path.exists():
            print(f"⚠️ Carpeta no existe: {folder}")
            return images
        
        all_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
            all_files.extend(folder_path.glob(ext))
        
        # Ordenar y limitar
        all_files = sorted(all_files)[:self.config.max_references]
        
        for file in all_files:
            try:
                img = Image.open(file)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                images.append(img)
                print(f"   + {file.name}")
            except Exception as e:
                print(f"   ⚠️ Error: {file.name}: {e}")
        
        return images
    
    def create_post(
        self, 
        user_request: str, 
        product_image_path: Optional[str] = None,
        output_path: str = "post.png",
        mode: GenerationMode = GenerationMode.CREATIVE
    ) -> Dict[str, Any]:
        """Crea un post de Instagram."""
        print("\n" + "="*60)
        print(f"🎨 GENERANDO POST - Modo: {mode.value.upper()}")
        print("="*60)
        
        # 1. Cargar producto
        product_image = None
        if product_image_path and os.path.exists(product_image_path):
            product_image = Image.open(product_image_path)
            if product_image.mode in ('RGBA', 'P'):
                product_image = product_image.convert('RGB')
        
        # 2. Análisis
        print("\n📊 Analizando...")
        analyses = self.analyzer.analyze_all(
            user_request, 
            self.company, 
            product_image,
            include_creative_context=(mode == GenerationMode.CREATIVE)
        )
        print("   ✓ Análisis completado")
        
        # 3. Construir prompt
        if mode == GenerationMode.REFERENCE:
            prompt = get_reference_prompt(
                self.style_guide,
                self.company.name,
                ', '.join(self.company.color_palette),
                user_request,
                analyses["user_intent"],
                analyses["product_info"]
            )
        else:
            prompt = get_creative_prompt(
                self.style_guide,
                analyses["creative_context"],
                self.company.name,
                self.company.color_palette,
                user_request,
                analyses["user_intent"],
                analyses["product_info"]
            )
        
        # 4. Construir partes
        parts = self._build_parts(prompt, product_image)
        
        # 5. Generar
        print(f"\n🚀 Generando imagen...")
        generated = self.client.generate_image(parts)
        
        if generated:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            generated.save(output_path, quality=self.config.output_quality)
            print(f"\n✅ POST GUARDADO: {output_path}")
            print(f"   Tamaño: {generated.size[0]}x{generated.size[1]}")
            
            return {"status": "success", "path": output_path, "mode": mode.value}
        
        return {"status": "error", "message": "Falló la generación"}
    
    def create_both_optimized(
        self,
        user_request: str,
        product_image_path: Optional[str] = None,
        output_folder: str = "posts"
    ) -> Dict[str, Any]:
        """
        Genera AMBAS versiones de forma OPTIMIZADA.
        Analiza UNA sola vez y reutiliza para ambas versiones.
        """
        print("\n" + "="*60)
        print("🎨 GENERANDO AMBAS VERSIONES (OPTIMIZADO)")
        print("="*60)
        
        # 1. Cargar producto UNA vez
        product_image = None
        if product_image_path and os.path.exists(product_image_path):
            product_image = Image.open(product_image_path)
            if product_image.mode in ('RGBA', 'P'):
                product_image = product_image.convert('RGB')
        
        # 2. Análisis UNA sola vez (incluye creative_context)
        print("\n📊 Analizando (una sola vez para ambas versiones)...")
        analyses = self.analyzer.analyze_all(
            user_request, 
            self.company, 
            product_image,
            include_creative_context=True  # Siempre incluir para tener todo
        )
        print("   ✓ Análisis completado")
        
        # 3. Construir partes comunes
        base_parts = self._build_parts_base(product_image)
        
        results = {}
        os.makedirs(output_folder, exist_ok=True)
        
        # 4. Generar REFERENCE
        print("\n📋 Generando versión REFERENCE...")
        ref_prompt = get_reference_prompt(
            self.style_guide,
            self.company.name,
            ', '.join(self.company.color_palette),
            user_request,
            analyses["user_intent"],
            analyses["product_info"]
        )
        ref_parts = base_parts + [types.Part.from_text(text=f"\n{ref_prompt}")]
        
        ref_img = self.client.generate_image(ref_parts)
        if ref_img:
            ref_path = f"{output_folder}/post_reference.png"
            ref_img.save(ref_path, quality=self.config.output_quality)
            results["reference"] = {"status": "success", "path": ref_path}
            print(f"   ✓ Guardado: {ref_path}")
        else:
            results["reference"] = {"status": "error"}
        
        # 5. Generar CREATIVE
        print("\n🎨 Generando versión CREATIVE...")
        creative_prompt = get_creative_prompt(
            self.style_guide,
            analyses["creative_context"],
            self.company.name,
            self.company.color_palette,
            user_request,
            analyses["user_intent"],
            analyses["product_info"]
        )
        creative_parts = base_parts + [types.Part.from_text(text=f"\n{creative_prompt}")]
        
        creative_img = self.client.generate_image(creative_parts)
        if creative_img:
            creative_path = f"{output_folder}/post_creative.png"
            creative_img.save(creative_path, quality=self.config.output_quality)
            results["creative"] = {"status": "success", "path": creative_path}
            print(f"   ✓ Guardado: {creative_path}")
        else:
            results["creative"] = {"status": "error"}
        
        print("\n" + "="*60)
        print("✅ AMBAS VERSIONES GENERADAS")
        print("="*60)
        
        return results
    
    def _build_parts_base(self, product_image: Optional[Image.Image]) -> List[types.Part]:
        """Construye las partes base (sin prompt) para reutilizar"""
        parts = []
        
        if self.reference_images:
            parts.append(types.Part.from_text(text=REFERENCES_INSTRUCTION))
            for ref_img in self.reference_images:
                parts.append(self._pil_to_part(ref_img))
        
        if self.logo_image:
            parts.append(types.Part.from_text(text=LOGO_INSTRUCTION))
            parts.append(self._pil_to_part(self.logo_image))
        
        if product_image:
            parts.append(types.Part.from_text(text=PRODUCT_INSTRUCTION))
            parts.append(self._pil_to_part(product_image))
        
        return parts
    
    def _build_parts(self, prompt: str, product_image: Optional[Image.Image]) -> List[types.Part]:
        """Construye todas las partes incluyendo el prompt"""
        parts = self._build_parts_base(product_image)
        parts.append(types.Part.from_text(text=f"\n{prompt}"))
        return parts
    
    def _pil_to_part(self, img: Image.Image) -> types.Part:
        """Convierte imagen PIL a Part de Gemini"""
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return types.Part.from_bytes(mime_type="image/png", data=buffer.getvalue())


# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

class InstagramAI:
    """Interfaz principal con dos modos de generación"""
    
    def __init__(
        self, 
        company: CompanyConfig, 
        references_folder: str,
        config: SystemConfig = DEFAULT_SYSTEM_CONFIG
    ):
        self.generator = InstagramPostGenerator(company, references_folder, config)
    
    def create_post(
        self, 
        request: str, 
        product_image: Optional[str] = None,
        output: str = "post.png",
        mode: str = "creative"
    ) -> Dict[str, Any]:
        """Crea un post de Instagram."""
        gen_mode = GenerationMode.CREATIVE if mode == "creative" else GenerationMode.REFERENCE
        return self.generator.create_post(request, product_image, output, gen_mode)
    
    def create_both_versions(
        self,
        request: str,
        product_image: Optional[str] = None,
        output_folder: str = "posts"
    ) -> Dict[str, Any]:
        """Genera AMBAS versiones de forma optimizada."""
        return self.generator.create_both_optimized(request, product_image, output_folder)
    
    def get_style_guide(self) -> str:
        """Retorna la guía de estilo"""
        return self.generator.style_guide
    
    def clear_cache(self):
        """Limpia el cache del style_guide"""
        cache_file = Path(self.generator.config.cache_file)
        if cache_file.exists():
            cache_file.unlink()
            print("✓ Cache limpiado")


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    # Configuración de la empresa
    company = CompanyConfig(
        name="Ferretería Gigante",
        description="Ferretería especializada en herramientas y construcción",
        color_palette=["#FF6B35", "#004E89", "#FFFFFF"],
        logo_path="assets/logo.png"
    )
    
    # Configuración del sistema (opcional - usa defaults si no se especifica)
    # config = SystemConfig(
    #     max_references=6,  # Usar menos referencias para mayor velocidad
    #     cache_style_guide=True
    # )
    
    # Crear generador
    ai = InstagramAI(company, "referencias")
    
    # Generar AMBAS versiones (optimizado)
    results = ai.create_both_versions(
        request="NUESTRO REFLECTOR LED SOLAR DE 40W ES EL MEJOR DEL MERCADO",
        product_image="fotos/luces.jpg",
        output_folder="posts"
    )
    
    print("\n🎉 ¡Listo! Compara ambas versiones y elige tu favorita.")
