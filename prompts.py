"""
Prompts del Sistema de Generación de Posts
⚠️ NO MODIFICAR - Estos prompts fueron optimizados cuidadosamente.
"""

from typing import List


# ============================================================================
# PROMPT: ANÁLISIS DE REFERENCIAS
# ============================================================================

ANALYZE_REFERENCES_PROMPT = """You are an expert graphic designer analyzing promotional Instagram posts.

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


# ============================================================================
# PROMPT: ANÁLISIS DE PRODUCTO (BÁSICO)
# ============================================================================

ANALYZE_PRODUCT_BASIC_PROMPT = """Analyze this product image:

1. What is this product? (brand, type, variant)
2. Main colors of the product/packaging
3. Shape and orientation
4. How should it be presented in a promotional post?

Be concise."""


# ============================================================================
# PROMPT: ANÁLISIS DE PRODUCTO (CONTEXTO CREATIVO)
# ============================================================================

ANALYZE_PRODUCT_CONTEXT_PROMPT = """Analyze this product image for CREATIVE CONTEXT generation:

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


# ============================================================================
# PROMPT: ANÁLISIS DE INTENCIÓN
# ============================================================================

def get_user_intent_prompt(company_name: str, company_description: str, colors: str, request: str) -> str:
    """Genera el prompt para analizar la intención del usuario"""
    return f"""Extract key information from this request:

COMPANY: {company_name}
ABOUT: {company_description}
BRAND COLORS: {colors}

USER REQUEST: "{request}"

Extract:
1. POST TYPE: (discount, promotion, new product, event, etc.)
2. MAIN MESSAGE: Headline text (max 5 words)
3. SECONDARY MESSAGE: Supporting text
4. KEY NUMBER/OFFER: Discount, price, or important number
5. CALL TO ACTION: What should viewers do?
6. URGENCY/DATE: Any deadline

Be concise."""


# ============================================================================
# PROMPT: GENERACIÓN MODO REFERENCE
# ============================================================================

def get_reference_prompt(style_guide: str, company_name: str, colors: str, 
                         user_request: str, user_intent: str, product_info: str) -> str:
    """Genera el prompt para modo REFERENCE"""
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
{style_guide}

══════════════════════════════════════════════════════════════════════
BRAND:
══════════════════════════════════════════════════════════════════════
Company: {company_name}
Brand Colors: {colors}

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
- DO NOT copy logos from the reference images - they are OTHER companies
- DO NOT add "DESLIZA", swipe buttons, or UI elements from references
- DO NOT add decorative elements like spirals that you see in references

⚠️ LOGO RULE (VERY IMPORTANT):
- Use ONLY the logo I provide labeled "COMPANY LOGO" - this is for {company_name}
- The logos you see in references (FERREMIX, TOLEDO, etc.) are OTHER companies
- IGNORE all logos in the reference images completely
- Show the provided {company_name} logo EXACTLY ONE TIME

══════════════════════════════════════════════════════════════════════
FINAL REQUIREMENT:
══════════════════════════════════════════════════════════════════════
Copy the STYLE from references (colors, layout, text effects, composition).
But use ONLY the logo I provide, not any logos from the references.
The image should go EDGE TO EDGE with NO border or frame.
The {company_name} logo appears ONLY ONCE."""


# ============================================================================
# PROMPT: GENERACIÓN MODO CREATIVE
# ============================================================================

def get_creative_prompt(style_guide: str, creative_context: str, company_name: str, 
                        colors: List[str], user_request: str, user_intent: str, 
                        product_info: str) -> str:
    """Genera el prompt para modo CREATIVE"""
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
{style_guide}

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
Company: {company_name}
Brand Colors: {', '.join(colors)}
- Use {colors[0]} for accents and highlights
- Use {colors[1]} for backgrounds or primary elements
- Use {colors[2]} for text

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
- DO NOT copy logos from the reference images - they are OTHER companies
- DO NOT add "DESLIZA", swipe buttons, or UI elements from references
- DO NOT add decorative elements like spirals from other brands

⚠️ LOGO RULE (VERY IMPORTANT):
- Use ONLY the logo I provide labeled "COMPANY LOGO"
- The logos you see in references (FERREMIX, TOLEDO, etc.) are OTHER companies
- IGNORE all logos in the reference images completely  
- Show the provided company logo EXACTLY ONE TIME in one corner
- NO duplicates, NO logos from references

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


# ============================================================================
# INSTRUCCIONES PARA PARTES DE IMAGEN
# ============================================================================

REFERENCES_INSTRUCTION = """══ REFERENCE IMAGES - STUDY THESE CAREFULLY ══
These images define the EXACT visual style you must replicate:
- Copy the TEXT EFFECTS (outlines, shadows, styling)
- Copy the BACKGROUND APPROACH (textures, colors, elements)
- Copy the PROMOTIONAL ELEMENT styles (banners, badges)
- Copy the LAYOUT and COMPOSITION patterns

⛔ CRITICAL RULES - READ CAREFULLY:
- NO border or frame around the final image
- Double-check spelling of all text

⚠️ LOGO RULES (VERY IMPORTANT):
- Use ONLY the company logo I provide (labeled "COMPANY LOGO")
- Do NOT copy any logos you see in the reference images
- The references show OTHER companies - IGNORE their logos completely
- Show the provided logo EXACTLY ONE TIME in one corner
- Do NOT add "DESLIZA", swipe icons, or other UI elements from references

The references are for STYLE only (colors, layout, text effects, composition).
NEVER copy the actual logos, brand names, or UI elements you see in them.
"""

LOGO_INSTRUCTION = """
══ COMPANY LOGO - THIS IS THE ONLY LOGO TO USE ══
Use THIS logo only. IGNORE all logos in the reference images.
The references show other companies (FERREMIX, TOLEDO, etc.) - do NOT use their logos.
Place this logo ONCE in one corner. No duplicates.
══════════════════════════════════════════════════"""

PRODUCT_INSTRUCTION = "\n══ PRODUCT IMAGE - Feature this prominently, keep recognizable ══"
