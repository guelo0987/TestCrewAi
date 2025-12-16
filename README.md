# 🎨 Instagram Post Generator con Gemini

Sistema inteligente para generar posts de Instagram personalizados usando IA generativa.

## 📋 ¿Cómo Funciona?

El sistema sigue un flujo de **2 fases**:

### Fase 1: Extracción de ADN Visual 🧬
Analiza las imágenes en la carpeta `referencias/` para extraer:
- **Patrones de estilo**: Composición, layout, uso del espacio
- **Uso del color**: Paletas, fondos, acentos
- **Tipografía**: Estilos, jerarquías, posicionamiento
- **Propósito e intención**: Tono, audiencia, call-to-action
- **Especificaciones técnicas**: Iluminación, efectos, formato

### Fase 2: Generación Inteligente 🚀
Combina el ADN Visual extraído con:
- Tu paleta de colores de marca
- Tu logo
- Tu producto/imagen
- Tu petición específica

Para generar un post único que **mantiene la coherencia visual** de tus referencias.

## 🛠️ Instalación

```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

1. Crea un archivo `.env` con tu API key de Gemini:
```
GEMINI_API_KEY=tu_api_key_aqui
```

2. Coloca tus imágenes de referencia en la carpeta `referencias/`
   - Estas son posts de Instagram que quieres usar como inspiración visual
   - Soporta: `.jpg`, `.jpeg`, `.png`, `.webp`

3. (Opcional) Coloca tu logo en `assets/logo.png`

## 🚀 Uso

```python
from main import InstagramAI, CompanyConfig

# Configura tu empresa/marca
company = CompanyConfig(
    name="Mi Empresa",
    description="Descripción de tu negocio",
    color_palette=["#FF6B35", "#004E89", "#F7F7F7"],
    logo_path="assets/logo.png"  # Opcional
)

# Inicializa el sistema (analiza las referencias automáticamente)
ai = InstagramAI(company, "referencias")

# Genera un post
result = ai.create_post(
    user_request="20% DESCUENTO en todos los productos. Estilo elegante.",
    product_image="mi_producto.png",  # Opcional
    output_path="posts/nuevo_post.png"
)

if result["status"] == "success":
    print(f"✅ Post generado: {result['path']}")
```

## 📁 Estructura de Carpetas

```
proyecto/
├── main.py              # Sistema principal
├── config.py            # Configuraciones
├── requirements.txt     # Dependencias
├── .env                 # API Key (crear manualmente)
├── referencias/         # 📌 Imágenes de referencia (tu estilo visual)
├── assets/
│   └── logo.png         # Tu logo
├── fotos/               # Tus productos/imágenes
└── posts/               # Posts generados (output)
```

## 💡 Consejos

1. **Mejores referencias = Mejores resultados**
   - Usa 3-6 imágenes de referencia con estilo consistente
   - Las imágenes deben representar el estilo que quieres lograr

2. **Sé específico en tu petición**
   - ❌ "Haz un post bonito"
   - ✅ "Post promocional con 20% descuento, estilo minimalista, texto grande"

3. **Paleta de colores**
   - Usa códigos hex exactos de tu marca
   - El sistema los integrará en el diseño

## 🔧 Modelos Utilizados

- **Análisis**: `gemini-2.5-flash` (rápido y preciso)
- **Generación de imágenes**: `gemini-2.0-flash-exp-image-generation`

## 📝 Licencia

MIT
