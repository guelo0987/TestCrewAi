"""
Servicio para interactuar con Google Gemini API
"""

import os
import io
from typing import List, Optional
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

from Services.config_service import SystemConfig

load_dotenv()


class GeminiService:
    """Servicio para interactuar con Gemini API"""
    
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
            
            if hasattr(response, 'text'):
                print(f"⚠️ Respuesta de texto: {response.text[:500]}...")
            return None
            
        except Exception as e:
            print(f"❌ Error generando imagen: {e}")
            return None
    
    def pil_to_part(self, img: Image.Image) -> types.Part:
        """Convierte imagen PIL a Part de Gemini (método público)"""
        return self._pil_to_part(img)

