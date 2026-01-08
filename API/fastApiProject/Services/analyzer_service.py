"""
Servicio para analizar imágenes y texto usando Gemini
"""

from typing import List
from PIL import Image

from Services.gemini_service import GeminiService
from Models import Empresa
from Utils.color_utils import ensure_colors_list

# Importar prompts desde el proyecto raíz
import os
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
    get_user_intent_prompt,
)


class AnalyzerService:
    """Servicio para analizar imágenes y texto"""
    
    def __init__(self, gemini_service: GeminiService):
        self.gemini = gemini_service
    
    def deep_analyze_references(self, images: List[Image.Image]) -> str:
        """Análisis exhaustivo de referencias"""
        return self.gemini.analyze_with_images(ANALYZE_REFERENCES_PROMPT, images)
    
    def analyze_product_basic(self, product_image: Image.Image) -> str:
        """Análisis básico del producto"""
        return self.gemini.analyze_with_images(ANALYZE_PRODUCT_BASIC_PROMPT, [product_image])
    
    def analyze_product_for_context(self, product_image: Image.Image) -> str:
        """Analiza el producto para contexto creativo"""
        return self.gemini.analyze_with_images(ANALYZE_PRODUCT_CONTEXT_PROMPT, [product_image])
    
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
        return self.gemini.analyze_text(prompt)
    
    def analyze_message_for_scratch(self, message: str, empresa: Empresa) -> str:
        """Analiza el mensaje para generar contenido desde cero"""
        prompt = ANALYZE_MESSAGE_PROMPT.format(
            message=message,
            company_name=empresa.nombre,
            company_description=empresa.descripcion or ""
        )
        return self.gemini.analyze_text(prompt)
    
    def analyze_post_for_regeneration(self, post_image: Image.Image) -> str:
        """Analiza un post existente para regenerarlo"""
        return self.gemini.analyze_with_images(ANALYZE_POST_FOR_REGENERATION_PROMPT, [post_image])
    
    def analyze_edit_request(self, edit_request: str) -> str:
        """Analiza la solicitud de edición"""
        prompt = ANALYZE_EDIT_REQUEST_PROMPT.format(edit_request=edit_request)
        return self.gemini.analyze_text(prompt)
    
    def analyze_multiple_products(self, product_images: List[Image.Image]) -> str:
        """Analiza múltiples productos"""
        num_products = len(product_images)
        prompt = ANALYZE_MULTIPLE_PRODUCTS_PROMPT.format(num_products=num_products)
        return self.gemini.analyze_with_images(prompt, product_images)
    
    def analyze_multiple_products_for_context(self, product_images: List[Image.Image]) -> str:
        """Analiza múltiples productos para contexto creativo"""
        contexts = []
        for i, img in enumerate(product_images, 1):
            context = self.gemini.analyze_with_images(ANALYZE_PRODUCT_CONTEXT_PROMPT, [img])
            contexts.append(f"PRODUCT {i}:\n{context}")
        return "\n\n".join(contexts)

