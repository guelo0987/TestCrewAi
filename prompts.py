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


# ============================================================================
# PROMPT: ANÁLISIS DE MENSAJE (PARA MODO SCRATCH)
# ============================================================================

ANALYZE_MESSAGE_PROMPT = """Analyze this message to create the perfect visual post:

MESSAGE: "{message}"
COMPANY: {company_name}
ABOUT: {company_description}

Your job is to determine EXACTLY what visual elements should be generated.
Be SPECIFIC and CREATIVE - no generic suggestions.

═══════════════════════════════════════════════════════════════
ANALYSIS REQUIRED:
═══════════════════════════════════════════════════════════════

1. MESSAGE ESSENCE:
   - What is the CORE message? (1 sentence)
   - What emotion should viewers feel?

2. VISUAL CONCEPT (BE SPECIFIC!):
   - Describe the EXACT imagery that represents this message
   - What should be the main visual element?
   - What background/setting makes sense?
   - What mood/atmosphere? (lighting, colors, style)
   
   Example thinking:
   - "Virgen de las Mercedes" → beautiful virgin statue with child, 
     heavenly rays, clouds, celestial atmosphere
   - "Cerrado por inventario" → warehouse with boxes, organized shelves,
     professional counting scene
   - "Nuevo servicio de llaves" → shiny keys, key cutting machine,
     professional locksmith imagery
   - "Llegaron los taladros DeWalt" → impressive power tools display,
     workshop setting, professional lighting

3. COMPOSITION SUGGESTIONS:
   - Where should the main visual element be?
   - What style? (realistic, illustrated, photographic)
   - What lighting? (dramatic, soft, bright, warm)

4. TEXT TO INCLUDE:
   - Extract the key text from the user's message
   - Keep it minimal - what are the essential words?

Be CREATIVE and SPECIFIC. Your visual description will be used to generate the image."""


# ============================================================================
# PROMPT: GENERACIÓN MODO SCRATCH
# ============================================================================

def get_scratch_prompt(style_guide: str, message_analysis: str, company_name: str,
                       colors: List[str], user_request: str, user_intent: str) -> str:
    """Genera el prompt para modo SCRATCH (sin imagen de producto)"""
    return f"""CREATE A BEAUTIFUL INSTAGRAM ANNOUNCEMENT POST (1:1 Square)

══════════════════════════════════════════════════════════════════════
MODE: SCRATCH - CLEAN & BEAUTIFUL ANNOUNCEMENT
══════════════════════════════════════════════════════════════════════

Create a STUNNING visual post. The IMAGE is the star - text is secondary.
Think like the Christmas post example: beautiful imagery, minimal text.

══════════════════════════════════════════════════════════════════════
📝 TEXT RULES (READ CAREFULLY!)
══════════════════════════════════════════════════════════════════════

USER'S EXACT MESSAGE: "{user_request}"

EXTRACT AND USE ONLY:
1. MAIN MESSAGE: The celebration/announcement (e.g., "Feliz Día de la Virgen de las Mercedes")
2. SCHEDULE INFO: Only if provided (e.g., "8am a 1pm")
3. COMPANY NAME: "{company_name}"

⛔ TEXT ERRORS TO AVOID:
- DO NOT duplicate words (like "8am a 8am a 1pm")
- DO NOT break words incorrectly (like "merc:des" or "de le les")
- DO NOT add random punctuation in the middle of words
- PROOFREAD the text before rendering - every word must be complete and correct
- Copy the user's text EXACTLY as written

🚨 SPELLING CHECK:
- "Mercedes" not "merc:des" or "mercides"
- "de las" not "de le les" or "de la les"
- Double-check EVERY word is spelled correctly

══════════════════════════════════════════════════════════════════════
🎨 VISUAL DESIGN (MOST IMPORTANT!)
══════════════════════════════════════════════════════════════════════

CREATE A BEAUTIFUL, IMMERSIVE VISUAL BASED ON THE MESSAGE CONTEXT.

The MESSAGE ANALYSIS below tells you EXACTLY what type of visual to create.
Follow that analysis - it was specifically generated for THIS message.

RULES:
- The visual should IMMEDIATELY communicate the message
- Create imagery that represents the THEME of the message
- Use relevant visual elements that make sense for this specific topic
- The visual should be so good that minimal text is needed
- Think: what image would perfectly represent this message?

DO NOT use generic stock-photo looks. Create something SPECIFIC to this message.

THE VISUAL SHOULD BE SO BEAUTIFUL THAT MINIMAL TEXT IS NEEDED.

══════════════════════════════════════════════════════════════════════
🖼️ LAYOUT & COMPOSITION
══════════════════════════════════════════════════════════════════════

- Image goes EDGE TO EDGE (no border, no frame, no margins)
- Text overlaid on the beautiful visual
- Logo in ONE corner only (use the logo I provide)
- Clean, uncluttered composition
- Text should have good contrast against background

══════════════════════════════════════════════════════════════════════
BRAND:
══════════════════════════════════════════════════════════════════════
Company: {company_name}
Colors: {', '.join(colors)}
- Use brand colors for text accents/outlines

══════════════════════════════════════════════════════════════════════
⛔ ABSOLUTELY DO NOT:
══════════════════════════════════════════════════════════════════════
1. ❌ NO BORDER or FRAME around the image - goes edge to edge
2. ❌ NO duplicated text or words
3. ❌ NO broken/split words with wrong characters
4. ❌ NO placeholder text like [DATE] or [TIME]
5. ❌ NO random icons floating (especially top corners)
6. ❌ NO invented information not in user's message
7. ❌ NO spelling mistakes - proofread everything

✅ DO:
1. ✅ Beautiful, immersive visual that fills the entire square
2. ✅ Minimal, clean text - let the image speak
3. ✅ Correct spelling of EVERY word
4. ✅ Logo appears ONCE only
5. ✅ Professional, polished result

══════════════════════════════════════════════════════════════════════
QUALITY CHECK BEFORE GENERATING:
══════════════════════════════════════════════════════════════════════
□ Is the visual beautiful and immersive?
□ Does the image go edge-to-edge with NO border?
□ Is every word spelled correctly?
□ Is there NO duplicated text?
□ Does the logo appear only ONCE?
□ Is the text minimal and clean?

Create something BEAUTIFUL that {company_name} would be proud to post."""


# ============================================================================
# PROMPT: ANÁLISIS DE POST EXISTENTE (PARA REGENERACIÓN)
# ============================================================================

ANALYZE_POST_FOR_REGENERATION_PROMPT = """Analyze this existing post that the user wants to REGENERATE with improvements.

Your job is to extract EVERYTHING about this post so we can create a BETTER version.

═══════════════════════════════════════════════════════════════
EXTRACT THE FOLLOWING:
═══════════════════════════════════════════════════════════════

1. MAIN MESSAGE/TEXT:
   - What is the headline text?
   - What is the secondary text?
   - Any prices, percentages, or offers shown?
   - Any dates or schedules mentioned?

2. PRODUCT/SUBJECT:
   - What product or subject is featured?
   - Brand name if visible?
   - Product type and characteristics?

3. VISUAL ELEMENTS:
   - What is the background? (color, photo, texture)
   - What visual elements are present? (splashes, effects, icons)
   - Layout structure? (diagonal, centered, split)

4. WHAT WORKS WELL:
   - What elements should be KEPT in the new version?
   - What visual choices are effective?

5. WHAT COULD BE IMPROVED:
   - Any issues with the current design?
   - Text problems? (spelling, placement, readability)
   - Logo issues? (duplicated, wrong position)
   - Visual issues? (cluttered, boring, off-brand)
   - Any borders or frames that shouldn't be there?

6. SUGGESTIONS FOR REGENERATION:
   - How could the next version be DIFFERENT but BETTER?
   - What alternative visual approach could work?
   - What should definitely CHANGE?

Be SPECIFIC and DETAILED. This analysis will be used to generate an improved version."""


# ============================================================================
# PROMPT: REGENERACIÓN DE POST
# ============================================================================

def get_regeneration_prompt(style_guide: str, post_analysis: str, company_name: str,
                            colors: List[str], feedback: str = "") -> str:
    """Genera el prompt para regenerar un post existente"""
    feedback_section = ""
    if feedback:
        feedback_section = f"""
══════════════════════════════════════════════════════════════════════
USER FEEDBACK (IMPORTANT - Address these issues):
══════════════════════════════════════════════════════════════════════
{feedback}

Make sure the new version FIXES these specific issues mentioned by the user.
"""
    
    return f"""REGENERATE THIS POST - CREATE A BETTER VERSION

══════════════════════════════════════════════════════════════════════
MODE: REGENERATION - IMPROVE THE PREVIOUS POST
══════════════════════════════════════════════════════════════════════

The user was not satisfied with the previous post. Create a NEW, BETTER version
that keeps what worked but IMPROVES what didn't.

══════════════════════════════════════════════════════════════════════
ANALYSIS OF PREVIOUS POST:
══════════════════════════════════════════════════════════════════════
{post_analysis}
{feedback_section}
══════════════════════════════════════════════════════════════════════
REGENERATION RULES:
══════════════════════════════════════════════════════════════════════

1. KEEP the same core MESSAGE and PRODUCT
2. KEEP the brand colors and logo
3. CHANGE the visual approach - make it DIFFERENT
4. FIX any issues identified in the analysis
5. Make it MORE PROFESSIONAL and POLISHED

Ideas for making it DIFFERENT:
- Try a different layout (if it was diagonal, try centered)
- Try a different background approach (if it was solid, try textured/photo)
- Try different text placement
- Add or remove visual elements
- Change the mood/energy (if it was busy, try minimal)

══════════════════════════════════════════════════════════════════════
STYLE GUIDE (follow this):
══════════════════════════════════════════════════════════════════════
{style_guide}

══════════════════════════════════════════════════════════════════════
BRAND:
══════════════════════════════════════════════════════════════════════
Company: {company_name}
Colors: {', '.join(colors)}

══════════════════════════════════════════════════════════════════════
⛔ CRITICAL RULES:
══════════════════════════════════════════════════════════════════════
1. ❌ NO BORDER or FRAME around the image
2. ❌ NO duplicated logos - ONLY ONE logo
3. ❌ NO spelling mistakes
4. ❌ NO duplicated text
5. ❌ NO placeholders like [DATE] or [TIME]
6. ✅ Image goes edge-to-edge
7. ✅ Logo appears EXACTLY ONCE
8. ✅ Professional, polished result
9. ✅ DIFFERENT from the previous version

══════════════════════════════════════════════════════════════════════
GOAL:
══════════════════════════════════════════════════════════════════════
Create a post that is NOTICEABLY DIFFERENT and BETTER than the previous one.
The user should see this and think "YES, this is much better!"

Keep the same message, but present it in a fresh, improved way."""
