"""
Sistema de Generación de Posts de Instagram - 100% Adaptativo
Dos modos: REFERENCIA (copia exacta) y CREATIVO (ambiente contextual)
Funciona para CUALQUIER tipo de empresa y estilo.
"""

import os
import io
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

class GenerationMode(Enum):
    """Modos de generación disponibles"""
    REFERENCE = "reference"  # Copia exacta del estilo de referencias
    CREATIVE = "creative"    # Ambiente contextual basado en producto/mensaje


@dataclass
class CompanyConfig:
    """Configuración de la empresa/marca"""
    name: str
    description: str
    color_palette: List[str]
    logo_path: Optional[str] = None


# ============================================================================
# CLIENTE GEMINI
# ============================================================================

class GeminiClient:
    """Cliente para Gemini"""
    
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
        self.vision_model = "gemini-2.5-flash"
        self.image_model = "gemini-2.5-flash-image"
    
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
            parts = []
            for img in images:
                parts.append(self._pil_to_part(img))
            parts.append(types.Part.from_text(text=prompt))
            
            contents = [types.Content(role="user", parts=parts)]
            
            response = self.client.models.generate_content(
                model=self.vision_model,
                contents=contents
            )
            return response.text
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return ""
    
    def analyze_text(self, prompt: str) -> str:
        """Análisis solo de texto"""
        try:
            contents = [types.Content(
                role="user", 
                parts=[types.Part.from_text(text=prompt)]
            )]
            
            response = self.client.models.generate_content(
                model=self.vision_model,
                contents=contents
            )
            return response.text
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return ""
    
    def generate_image(self, parts: List[types.Part]) -> Optional[Image.Image]:
        """Genera imagen con configuración 1:1"""
        try:
            contents = [types.Content(role="user", parts=parts)]
            
            generate_config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(
                    aspect_ratio="1:1",
                ),
            )
            
            response = self.client.models.generate_content(
                model=self.image_model,
                contents=contents,
                config=generate_config
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
# ANALIZADOR ADAPTATIVO
# ============================================================================

class AdaptiveAnalyzer:
    """Analizador 100% adaptativo"""
    
    def __init__(self, client: GeminiClient):
        self.client = client
    
    def deep_analyze_references(self, images: List[Image.Image]) -> str:
        """Análisis exhaustivo de TODAS las referencias"""
        prompt = """You are an expert graphic designer analyzing promotional Instagram posts.

Analyze ALL these reference images and extract a COMPREHENSIVE STYLE GUIDE.

⚠️ PAY SPECIAL ATTENTION TO THESE CRITICAL ELEMENTS:

## 1. TEXT EFFECTS (CRITICAL!)
- Do texts have OUTLINE/STROKE effects? What color is the outline?
- Do texts have SHADOW effects? What type?
- Do texts have 3D or emboss effects?
- What is the exact style of the main headline text?
- Describe the text treatment in DETAIL - this is crucial for replication

## 2. LOGO TREATMENT (CRITICAL!)
- WHERE exactly is the logo positioned? (which corner, top/bottom)
- Does the logo have a BACKGROUND SHAPE? (circle, rectangle, none)
- What COLOR is the logo background shape?
- What SIZE is the logo relative to the composition?
- Is the logo on a colored circle/badge? DESCRIBE EXACTLY.

## 3. BACKGROUND STYLE (CRITICAL!)
- Is the background a SOLID color, GRADIENT, TEXTURE, or PHOTO?
- If texture: what kind? (marble, concrete, subtle pattern, etc.)
- If photo: what type of photo? (contextual, lifestyle, abstract)
- Are there DIAGONAL ELEMENTS or geometric shapes in backgrounds?
- Specific background colors with hex codes

## 4. TYPOGRAPHY DETAILS
- Font family style (sans-serif bold, serif, script, display)
- Size hierarchy (headline vs subtext proportions)
- Text colors with hex codes
- Text positioning (centered, left-aligned, specific areas)

## 5. PROMOTIONAL ELEMENTS
- How are PERCENTAGES/DISCOUNTS displayed? (size, color, container shape)
- What BANNERS or BADGES are used? (shape, color, position)
- How is VALIDITY/DATE info shown? (banner at bottom? text style?)
- Call-to-action button styles if any

## 6. PRODUCT PRESENTATION
- How are products displayed? (cutout, with shadow, with effects)
- Size and position in composition
- Any decorative elements around products?

## 7. COLOR PALETTE
- List ALL colors with hex codes
- Which color dominates the backgrounds?
- Which color is used for accents/highlights?
- Which color is used for primary text?

## 8. OVERALL PATTERNS
- Common layout structures (split diagonal, centered, asymmetric)
- Visual hierarchy flow
- Consistent elements across all references

Be EXTREMELY specific and technical. Include exact details about outlines, shadows, shapes, and positions. This guide will be used to generate IDENTICAL style posts."""

        return self.client.analyze_with_images(prompt, images)
    
    def analyze_product_for_context(self, product_image: Image.Image) -> str:
        """Analiza el producto para generar contexto creativo"""
        prompt = """Analyze this product image for CREATIVE CONTEXT generation:

1. PRODUCT TYPE
- What is this product? (category, brand, use)

2. ASSOCIATED ENVIRONMENT
- What environment/context is this product used in?
- What visual elements represent this product's world?
- Example: Paint → splashes, brushes, colorful drips
- Example: Tools → workshop, construction, sparks
- Example: Plumbing → water, pipes, bathroom

3. MOOD/ENERGY
- What feeling should the post convey?
- Dynamic, professional, playful, serious?

4. SUGGESTED CREATIVE ELEMENTS
- What background elements would make sense for this product?
- What textures, patterns, or effects fit?

5. COLOR ASSOCIATIONS
- What colors are associated with this product type?
- What complementary elements could enhance it?

Be creative but relevant. The suggestions should make visual sense."""

        return self.client.analyze_with_images(prompt, [product_image])
    
    def analyze_product_basic(self, product_image: Image.Image) -> str:
        """Análisis básico del producto"""
        prompt = """Analyze this product image:

1. What is this product? (brand, type, variant)
2. Main colors of the product/packaging
3. Shape and orientation
4. How should it be presented in a promotional post?

Be concise."""

        return self.client.analyze_with_images(prompt, [product_image])
    
    def analyze_user_intent(self, request: str, company: CompanyConfig) -> str:
        """Analiza la intención del usuario"""
        prompt = f"""Extract key information from this request:

COMPANY: {company.name}
ABOUT: {company.description}
BRAND COLORS: {', '.join(company.color_palette)}

USER REQUEST: "{request}"

Extract:
1. POST TYPE: (discount, promotion, new product, event, etc.)
2. MAIN MESSAGE: Headline text (max 5 words)
3. SECONDARY MESSAGE: Supporting text
4. KEY NUMBER/OFFER: Discount, price, or important number
5. CALL TO ACTION: What should viewers do?
6. URGENCY/DATE: Any deadline

Be concise."""

        return self.client.analyze_text(prompt)


# ============================================================================
# GENERADOR DE POSTS
# ============================================================================

class InstagramPostGenerator:
    """Genera posts con dos modos: REFERENCE y CREATIVE"""
    
    def __init__(self, company: CompanyConfig, references_folder: str):
        self.client = GeminiClient()
        self.company = company
        self.references_folder = references_folder
        self.analyzer = AdaptiveAnalyzer(self.client)
        
        self.reference_images: List[Image.Image] = []
        self.style_guide: str = ""
        self.logo_image: Optional[Image.Image] = None
        
        self._initialize()
    
    def _initialize(self):
        """Inicializa el sistema"""
        print("\n" + "="*60)
        print("🔧 INICIALIZANDO SISTEMA")
        print("="*60)
        
        print(f"\n📂 Cargando referencias de: {self.references_folder}")
        self.reference_images = self._load_all_images(self.references_folder)
        print(f"   ✓ {len(self.reference_images)} imágenes cargadas")
        
        if self.reference_images:
            print(f"\n🔍 Analizando referencias...")
            self.style_guide = self.analyzer.deep_analyze_references(self.reference_images)
            print("   ✓ Guía de estilo extraída")
        
        if self.company.logo_path and os.path.exists(self.company.logo_path):
            self.logo_image = Image.open(self.company.logo_path)
            if self.logo_image.mode in ('RGBA', 'P'):
                self.logo_image = self.logo_image.convert('RGB')
            print(f"   ✓ Logo cargado")
        
        print("\n✅ Sistema listo\n")
    
    def _load_all_images(self, folder: str) -> List[Image.Image]:
        """Carga todas las imágenes"""
        images = []
        folder_path = Path(folder)
        
        if not folder_path.exists():
            print(f"⚠️ Carpeta no existe: {folder}")
            return images
        
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.webp']:
            for file in sorted(folder_path.glob(ext)):
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
        """
        Crea un post de Instagram.
        
        Args:
            user_request: Lo que el usuario quiere comunicar
            product_image_path: Ruta a la imagen del producto
            output_path: Donde guardar el resultado
            mode: REFERENCE (copia exacta) o CREATIVE (ambiente contextual)
        """
        print("\n" + "="*60)
        print(f"🎨 GENERANDO POST - Modo: {mode.value.upper()}")
        print("="*60)
        
        # 1. Analizar intención
        print("\n💭 Analizando solicitud...")
        user_intent = self.analyzer.analyze_user_intent(user_request, self.company)
        
        # 2. Analizar producto
        product_image = None
        product_info = ""
        creative_context = ""
        
        if product_image_path and os.path.exists(product_image_path):
            print(f"\n📦 Analizando producto...")
            product_image = Image.open(product_image_path)
            if product_image.mode in ('RGBA', 'P'):
                product_image = product_image.convert('RGB')
            
            product_info = self.analyzer.analyze_product_basic(product_image)
            
            # Solo para modo CREATIVE, analizamos contexto creativo
            if mode == GenerationMode.CREATIVE:
                print("   🎨 Analizando contexto creativo...")
                creative_context = self.analyzer.analyze_product_for_context(product_image)
        
        # 3. Construir prompt según el modo
        if mode == GenerationMode.REFERENCE:
            prompt = self._build_reference_prompt(user_request, user_intent, product_info)
        else:
            prompt = self._build_creative_prompt(user_request, user_intent, product_info, creative_context)
        
        print("\n📝 PROMPT:")
        print("-"*40)
        print(prompt[:1500] + "..." if len(prompt) > 1500 else prompt)
        print("-"*40)
        
        # 4. Construir partes
        parts = self._build_parts(prompt, product_image, mode)
        
        # 5. Generar
        print(f"\n🚀 Generando imagen...")
        generated = self.client.generate_image(parts)
        
        if generated:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            generated.save(output_path, quality=95)
            print(f"\n✅ POST GUARDADO: {output_path}")
            print(f"   Tamaño: {generated.size[0]}x{generated.size[1]}")
            print(f"   Modo: {mode.value}")
            
            return {"status": "success", "path": output_path, "mode": mode.value}
        else:
            return {"status": "error", "message": "Falló la generación"}
    
    def _build_reference_prompt(
        self, 
        user_request: str,
        user_intent: str,
        product_info: str
    ) -> str:
        """Prompt para modo REFERENCE - copia exacta del estilo"""
        return f"""CREATE A PROMOTIONAL INSTAGRAM POST (1:1 Square)

══════════════════════════════════════════════════════════════════════
MODE: REFERENCE - EXACT STYLE REPLICATION (100% MATCH)
══════════════════════════════════════════════════════════════════════

Your task is to create a post that is VISUALLY IDENTICAL to the references.
Someone should NOT be able to tell your output from the reference images.

══════════════════════════════════════════════════════════════════════
⚠️ CRITICAL: COPY THESE ELEMENTS EXACTLY
══════════════════════════════════════════════════════════════════════

1. TEXT EFFECTS:
   - If references have text with OUTLINE/STROKE → add outline
   - If references have text with SHADOW → add shadow
   - Copy the EXACT font weight and style
   - Match text positioning patterns

2. LOGO TREATMENT:
   - Place logo in the EXACT same position as references
   - If logo appears on a COLORED CIRCLE/SHAPE → replicate that
   - Match the exact size ratio

3. BACKGROUNDS:
   - If references use TEXTURES → use similar textures
   - If references use PHOTOS → use contextual photos
   - Copy diagonal elements or geometric shapes if present
   - Match the exact color palette

4. PROMOTIONAL ELEMENTS:
   - Copy how discounts/prices are styled
   - Replicate banner and badge styles exactly
   - Match date/validity info placement and style

══════════════════════════════════════════════════════════════════════
STYLE GUIDE (extracted from references - REPLICATE THIS):
══════════════════════════════════════════════════════════════════════
{self.style_guide}

══════════════════════════════════════════════════════════════════════
BRAND:
══════════════════════════════════════════════════════════════════════
Company: {self.company.name}
Brand Colors: {', '.join(self.company.color_palette)}

══════════════════════════════════════════════════════════════════════
CONTENT TO INCLUDE:
══════════════════════════════════════════════════════════════════════
Request: "{user_request}"

Intent Analysis:
{user_intent}

Product Info:
{product_info}

══════════════════════════════════════════════════════════════════════
⛔ DO NOT (CRITICAL - READ CAREFULLY):
══════════════════════════════════════════════════════════════════════
- DO NOT add any border or frame around the image
- DO NOT make spelling mistakes - double check all text
- ⚠️ LOGO RULE: The company logo must appear EXACTLY ONE TIME in the entire image.
  Do NOT add a second logo, mini logo, or logo icon anywhere else.
  Pick ONE position for the logo and that's it. NO DUPLICATES.

══════════════════════════════════════════════════════════════════════
FINAL REQUIREMENT:
══════════════════════════════════════════════════════════════════════
The output MUST be INDISTINGUISHABLE from the reference images.
Copy every visual detail: text effects, logo placement, backgrounds,
promotional element styles, color usage, and composition patterns.
The image should go EDGE TO EDGE with NO border or frame.
The logo appears ONLY ONCE - not twice, not a big one and a small one."""

    def _build_creative_prompt(
        self, 
        user_request: str,
        user_intent: str,
        product_info: str,
        creative_context: str
    ) -> str:
        """Prompt para modo CREATIVE - ambiente contextual"""
        return f"""CREATE A PROMOTIONAL INSTAGRAM POST (1:1 Square)

══════════════════════════════════════════════════════════════════════
MODE: CREATIVE - CONTEXTUAL ENVIRONMENT WITH REFERENCE STYLE
══════════════════════════════════════════════════════════════════════

Your task is to create a post that:
1. MATCHES the exact STYLE ELEMENTS of the references (text effects, logo treatment, etc.)
2. ADDS creative contextual elements that relate to the product
3. Combines professional reference style with product-relevant creativity

══════════════════════════════════════════════════════════════════════
⚠️ MANDATORY STYLE ELEMENTS (copy EXACTLY from references):
══════════════════════════════════════════════════════════════════════

1. TEXT TREATMENT:
   - Apply the SAME text effects as references (outline/stroke if they have it)
   - Use the SAME font weight and style
   - Match the SAME size hierarchy
   
2. LOGO PLACEMENT:
   - Position the logo EXACTLY as shown in references
   - If references show logo in a colored circle/shape, DO THE SAME
   - Match the exact corner/position used in references

3. BACKGROUND APPROACH:
   - If references use textures, use similar textures
   - If references use diagonal elements, include them
   - Match the background color scheme

4. PROMOTIONAL ELEMENTS:
   - Style discounts/percentages the same way as references
   - Use similar banner/badge styles for dates/validity
   - Match the promotional element colors and shapes

══════════════════════════════════════════════════════════════════════
STYLE GUIDE (extracted from references - FOLLOW THIS):
══════════════════════════════════════════════════════════════════════
{self.style_guide}

══════════════════════════════════════════════════════════════════════
CREATIVE ADDITIONS (based on product - ADD THESE):
══════════════════════════════════════════════════════════════════════
{creative_context}

Add contextual elements that make sense for this product:
- Paint → splashes, drips, brush strokes in brand colors
- Tools → workshop vibes, sparks, construction elements
- Plumbing → water elements, pipe imagery
- Electrical → energy effects, light elements

These creative elements should ENHANCE the design while maintaining 
the professional style of the references.

══════════════════════════════════════════════════════════════════════
BRAND:
══════════════════════════════════════════════════════════════════════
Company: {self.company.name}
Brand Colors: {', '.join(self.company.color_palette)}
- Use {self.company.color_palette[0]} for accents and highlights
- Use {self.company.color_palette[1]} for backgrounds or primary elements
- Use {self.company.color_palette[2]} for text

══════════════════════════════════════════════════════════════════════
CONTENT:
══════════════════════════════════════════════════════════════════════
Request: "{user_request}"

Intent Analysis:
{user_intent}

Product Info:
{product_info}

══════════════════════════════════════════════════════════════════════
⛔ DO NOT (CRITICAL - READ CAREFULLY):
══════════════════════════════════════════════════════════════════════
- DO NOT add any BORDER or FRAME around the image - image goes edge to edge
- DO NOT make spelling mistakes - verify all text carefully
- DO NOT add unnecessary decorative borders
- ⚠️ LOGO RULE: The company logo must appear EXACTLY ONE TIME in the entire image.
  Do NOT add a second logo, mini logo, watermark, or logo icon anywhere else.
  Pick ONE corner/position for the logo and that's it. NO DUPLICATES ANYWHERE.

══════════════════════════════════════════════════════════════════════
FINAL REQUIREMENTS:
══════════════════════════════════════════════════════════════════════
1. ✅ Match reference TEXT STYLE (outlines, shadows, effects)
2. ✅ Match reference LOGO TREATMENT (position, background shape)
3. ✅ Match reference BACKGROUND APPROACH (textures, colors)
4. ✅ Match reference PROMOTIONAL STYLE (banners, badges)
5. ✅ ADD creative contextual elements for this specific product
6. ✅ Keep product prominent and recognizable
7. ✅ Professional quality matching references
8. ✅ NO BORDER/FRAME - content goes to the edges
9. ✅ LOGO appears ONLY ONCE
10. ✅ CORRECT SPELLING on all text

The output should look like it belongs to the SAME CAMPAIGN as the 
references, but with added creative elements relevant to this product."""

    def _build_parts(
        self, 
        prompt: str, 
        product_image: Optional[Image.Image],
        mode: GenerationMode
    ) -> List[types.Part]:
        """Construye las partes para enviar al modelo"""
        parts = []
        
        # Referencias con instrucciones claras
        if self.reference_images:
            parts.append(types.Part.from_text(
                text="""══ REFERENCE IMAGES - STUDY THESE CAREFULLY ══
These images define the EXACT visual style you must replicate:
- Copy the TEXT EFFECTS (outlines, shadows, styling)
- Copy the LOGO PLACEMENT and background shape
- Copy the BACKGROUND APPROACH (textures, colors, elements)
- Copy the PROMOTIONAL ELEMENT styles (banners, badges)

⛔ CRITICAL RULES:
- NO border or frame around the final image
- Double-check spelling of all text
- ⚠️ LOGO: Show the logo EXACTLY ONE TIME. Pick one corner/position.
  Do NOT add a second smaller logo or icon elsewhere. ONE LOGO ONLY.
"""
            ))
            for ref_img in self.reference_images:
                parts.append(self._pil_to_part(ref_img))
        
        # Logo con instrucción
        if self.logo_image:
            parts.append(types.Part.from_text(
                text="\n══ COMPANY LOGO - Place this ONCE in one corner. DO NOT duplicate. ══"
            ))
            parts.append(self._pil_to_part(self.logo_image))
        
        # Producto con instrucción
        if product_image:
            parts.append(types.Part.from_text(
                text="\n══ PRODUCT IMAGE - Feature this prominently, keep recognizable ══"
            ))
            parts.append(self._pil_to_part(product_image))
        
        # Prompt
        parts.append(types.Part.from_text(text=f"\n{prompt}"))
        
        return parts
    
    def _pil_to_part(self, img: Image.Image) -> types.Part:
        """Convierte imagen PIL a Part de Gemini"""
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return types.Part.from_bytes(
            mime_type="image/png",
            data=buffer.getvalue()
        )


# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

class InstagramAI:
    """Interfaz principal con dos modos de generación"""
    
    def __init__(self, company: CompanyConfig, references_folder: str):
        self.generator = InstagramPostGenerator(company, references_folder)
    
    def create_post(
        self, 
        request: str, 
        product_image: Optional[str] = None,
        output: str = "post.png",
        mode: str = "creative"  # "reference" o "creative"
    ) -> Dict[str, Any]:
        """
        Crea un post de Instagram.
        
        Args:
            request: Lo que quieres comunicar
            product_image: Ruta a la imagen del producto
            output: Donde guardar el resultado
            mode: "reference" (copia exacta) o "creative" (ambiente contextual)
        """
        gen_mode = GenerationMode.CREATIVE if mode == "creative" else GenerationMode.REFERENCE
        return self.generator.create_post(request, product_image, output, gen_mode)
    
    def create_both_versions(
        self,
        request: str,
        product_image: Optional[str] = None,
        output_folder: str = "posts"
    ) -> Dict[str, Any]:
        """
        Genera AMBAS versiones para que el usuario elija.
        
        Returns:
            Dict con paths de ambas versiones
        """
        print("\n" + "="*60)
        print("🎨 GENERANDO AMBAS VERSIONES")
        print("="*60)
        
        results = {}
        
        # Versión REFERENCE
        print("\n📋 Generando versión REFERENCE...")
        ref_result = self.generator.create_post(
            request, 
            product_image, 
            f"{output_folder}/post_reference.png",
            GenerationMode.REFERENCE
        )
        results["reference"] = ref_result
        
        # Versión CREATIVE
        print("\n🎨 Generando versión CREATIVE...")
        creative_result = self.generator.create_post(
            request, 
            product_image, 
            f"{output_folder}/post_creative.png",
            GenerationMode.CREATIVE
        )
        results["creative"] = creative_result
        
        print("\n" + "="*60)
        print("✅ AMBAS VERSIONES GENERADAS")
        print("="*60)
        print(f"   📋 Reference: {results['reference'].get('path', 'Error')}")
        print(f"   🎨 Creative:  {results['creative'].get('path', 'Error')}")
        
        return results
    
    def get_style_guide(self) -> str:
        """Retorna la guía de estilo"""
        return self.generator.style_guide


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    # Configuración
    company = CompanyConfig(
        name="Ferretería Gigante",
        description="Ferretería especializada en herramientas y construcción",
        color_palette=["#FF6B35", "#004E89", "#FFFFFF"],
        logo_path="assets/logo.png"
    )
    
    # Crear generador
    ai = InstagramAI(company, "referencias")
    
    # Opción 1: Generar una versión específica
    # result = ai.create_post(
    #     request="10% DE DESCUENTO EN PINTURAS TROPICAL. Promoción válida hasta fin de mes.",
    #     product_image="fotos/tropical.png",
    #     output="posts/mi_post.png",
    #     mode="creative"  # o "reference"
    # )
    
    # Opción 2: Generar AMBAS versiones para comparar
    results = ai.create_both_versions(
        request="NUESTRO REFLECTOR LED SOLAR DE 40W ES EL MEJOR DEL MERCADO",
        product_image="fotos/luces.jpg",
        output_folder="posts"
    )
    
    print("\n🎉 ¡Listo! Compara ambas versiones y elige tu favorita.")
