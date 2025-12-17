# 🎨 Instagram Post Generator - AI Powered

Sistema de generación de posts de Instagram potenciado por **Google Gemini AI**. Genera posts profesionales que mantienen consistencia de marca basándose en imágenes de referencia.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Flujo de Funcionamiento](#-flujo-de-funcionamiento)
- [Modos de Generación](#-modos-de-generación)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Configuración](#-configuración)
- [Estructura de Archivos](#-estructura-de-archivos)
- [API Reference](#-api-reference)

---

## ✨ Características

- **100% Adaptativo**: Funciona para cualquier tipo de empresa y producto
- **3 Modos de Generación**: Reference, Creative y Scratch
- **Análisis Inteligente**: Extrae automáticamente el estilo de las referencias
- **Cache Inteligente**: Evita re-análisis innecesarios
- **Sin Hardcoding**: No depende de keywords o categorías fijas
- **Consistencia de Marca**: Todos los posts siguen el mismo estilo visual

---

## 🏗 Arquitectura

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                        InstagramAI                               │
│                    (Interfaz Principal)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  InstagramPostGenerator                          │
│                   (Motor de Generación)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Referencias │  │    Logo     │  │     Style Guide         │  │
│  │  (imágenes) │  │  (imagen)   │  │ (texto extraído)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AdaptiveAnalyzer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Análisis Refs   │  │ Análisis Prod   │  │ Análisis Intent │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       GeminiClient                               │
│           (Comunicación con Google Gemini API)                   │
│  ┌─────────────────┐              ┌─────────────────┐           │
│  │  Vision Model   │              │  Image Model    │           │
│  │ (gemini-2.5-flash)             │ (gemini-2.5-flash-image)    │
│  └─────────────────┘              └─────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Archivos del Sistema

| Archivo | Descripción |
|---------|-------------|
| `main.py` | Motor principal de generación |
| `config.py` | Configuraciones y dataclasses |
| `prompts.py` | Todos los prompts del sistema |
| `.env` | Variables de entorno (API key) |

---

## 🔄 Flujo de Funcionamiento

### Fase 1: Inicialización (Una sola vez)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Cargar     │ ──▶ │   Analizar   │ ──▶ │   Extraer    │
│ Referencias  │     │  Referencias │     │ Style Guide  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │   Guardar    │
                                          │   en Cache   │
                                          └──────────────┘
```

**Paso 1: Cargar Referencias**
```python
self.reference_images = self._load_images("referencias/")
# Carga hasta max_references imágenes (default: 20)
```

**Paso 2: Analizar Referencias**
```python
self.style_guide = self.analyzer.deep_analyze_references(self.reference_images)
```

Gemini Vision analiza todas las referencias y extrae:
- **Efectos de texto**: Outlines, sombras, 3D
- **Tratamiento del logo**: Posición, forma de fondo, tamaño
- **Estilo de fondo**: Diagonales, texturas, colores
- **Tipografía**: Fuentes, tamaños, jerarquía
- **Elementos promocionales**: Banners, badges, CTAs
- **Paleta de colores**: Colores primarios, secundarios, acentos

**Paso 3: Cache**
```python
# Si las referencias no cambiaron, usa el cache
cached = self.cache.get_cached("referencias/")
```

---

### Fase 2: Generación (Cada post)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Mensaje    │ ──▶ │   Analizar   │ ──▶ │   Construir  │
│  del Usuario │     │   Intención  │     │    Prompt    │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                           ┌─────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────┐
│                    Partes de la Imagen                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────┐ │
│  │Referencias │ │   Logo     │ │  Producto  │ │ Prompt │ │
│  │ (imágenes) │ │  (imagen)  │ │  (imagen)  │ │ (texto)│ │
│  └────────────┘ └────────────┘ └────────────┘ └────────┘ │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
                  ┌──────────────┐
                  │   Gemini     │
                  │  Genera      │
                  │   Imagen     │
                  └──────────────┘
                           │
                           ▼
                  ┌──────────────┐
                  │  POST FINAL  │
                  │   (1:1 PNG)  │
                  └──────────────┘
```

---

## 🎯 Modos de Generación

### 1. Modo REFERENCE
**Propósito**: Copia exacta del estilo de las referencias

```python
result = ai.create_post(
    request="10% de descuento en pinturas",
    product_image="fotos/pintura.png",
    output="post.png",
    mode="reference"
)
```

**Características**:
- Replica exactamente los efectos de texto
- Copia la posición y tratamiento del logo
- Usa los mismos patrones de layout
- Ideal para mantener consistencia absoluta

---

### 2. Modo CREATIVE
**Propósito**: Estilo de referencias + contexto creativo del producto

```python
result = ai.create_post(
    request="Nuestra aspiradora inalámbrica de 20V",
    product_image="fotos/aspiradora.png",
    output="post.png",
    mode="creative"
)
```

**Características**:
- Mantiene el estilo visual de las referencias
- Añade elementos contextuales del producto
- Ejemplo: Aspiradora → fondo con interior de carro
- Más dinámico y atractivo visualmente

---

### 3. Modo SCRATCH
**Propósito**: Genera todo desde cero basándose solo en el mensaje

```python
result = ai.create_scratch(
    request="Mañana no abrimos por la tormenta tropical Melissa",
    output="post_scratch.png"
)
```

**Características**:
- No requiere imagen de producto
- Genera visual apropiado para el mensaje
- Ejemplos de uso:
  - Anuncios de cierre
  - Celebraciones religiosas/festivas
  - Cambios de horario
  - Emergencias climáticas
  - Felicitaciones

---

### Función Optimizada: Ambas Versiones

```python
results = ai.create_both_versions(
    request="10% de descuento en taladros",
    product_image="fotos/taladro.png",
    output_folder="posts"
)
# Genera: posts/post_reference.png y posts/post_creative.png
```

**Ventajas**:
- Analiza UNA sola vez
- Reutiliza análisis para ambas versiones
- Más rápido y eficiente

---

### 4. Modo REGENERATE
**Propósito**: Regenera un post existente que no gustó, creando una versión mejorada

```python
result = ai.regenerate(
    existing_post="posts/post_creative.png",
    output="posts/post_v2.png",
    feedback="No me gustó el fondo, quiero algo más limpio"
)
```

**Cómo funciona**:
1. Analiza el post existente (extrae mensaje, producto, elementos visuales)
2. Identifica qué funciona bien y qué podría mejorar
3. Genera una versión DIFERENTE y MEJOR
4. Mantiene el mismo mensaje y producto, pero cambia el enfoque visual

**Casos de uso**:
- El cliente no quedó satisfecho con el resultado
- Quieres probar un estilo diferente
- El post original tenía errores (logo duplicado, texto mal, etc.)
- Quieres opciones alternativas para elegir

**Parámetros**:
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| existing_post | str | Ruta al post que se quiere regenerar |
| output | str | Ruta de salida para el nuevo post |
| feedback | str | Comentarios sobre qué mejorar |

---

## 📦 Instalación

### 1. Clonar repositorio
```bash
git clone <repo-url>
cd TestCrewAi
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar API Key
```bash
# Crear archivo .env
echo "GEMINI_API_KEY=tu-api-key-aqui" > .env
```

### 5. Preparar carpetas
```
proyecto/
├── referencias/      # Imágenes de referencia (posts existentes)
├── fotos/           # Imágenes de productos
├── assets/          # Logo de la empresa
│   └── logo.png
└── posts/           # Carpeta de salida (se crea automáticamente)
```

---

## 🚀 Uso

### Uso Básico

```python
from main import InstagramAI
from config import CompanyConfig

# Configurar empresa
company = CompanyConfig(
    name="Mi Ferretería",
    description="Venta de herramientas y materiales de construcción",
    color_palette=["#FF6B35", "#004E89", "#FFFFFF"],
    logo_path="assets/logo.png"
)

# Crear generador
ai = InstagramAI(company, "referencias")

# Generar post con producto
result = ai.create_post(
    request="20% de descuento en taladros DeWalt",
    product_image="fotos/taladro.png",
    output="mi_post.png",
    mode="creative"
)

# Generar post sin producto (scratch)
result = ai.create_scratch(
    request="Feliz Navidad a todos nuestros clientes",
    output="post_navidad.png"
)

# Generar ambas versiones
results = ai.create_both_versions(
    request="Nueva línea de pinturas",
    product_image="fotos/pintura.png",
    output_folder="posts"
)
```

### Ejecutar desde Terminal

```bash
python main.py
```

---

## ⚙️ Configuración

### CompanyConfig

```python
@dataclass
class CompanyConfig:
    name: str                    # Nombre de la empresa
    description: str             # Descripción del negocio
    color_palette: List[str]     # Colores de marca [primario, secundario, texto]
    logo_path: Optional[str]     # Ruta al logo
```

### SystemConfig

```python
@dataclass
class SystemConfig:
    vision_model: str = "gemini-2.5-flash"        # Modelo para análisis
    image_model: str = "gemini-2.5-flash-image"   # Modelo para generación
    max_references: int = 20                       # Máx referencias a cargar
    cache_style_guide: bool = True                 # Usar cache
    cache_file: str = ".style_guide_cache.json"   # Archivo de cache
    aspect_ratio: str = "1:1"                      # Relación de aspecto
    output_quality: int = 95                       # Calidad JPEG/PNG
```

### Ejemplo con Configuración Personalizada

```python
from config import SystemConfig

config = SystemConfig(
    max_references=10,          # Usar menos referencias (más rápido)
    cache_style_guide=True,     # Activar cache
    aspect_ratio="1:1"          # Instagram cuadrado
)

ai = InstagramAI(company, "referencias", config)
```

---

## 📁 Estructura de Archivos

```
TestCrewAi/
│
├── main.py                 # Motor principal
│   ├── GeminiClient        # Comunicación con API
│   ├── AdaptiveAnalyzer    # Análisis de referencias/productos
│   ├── StyleGuideCache     # Sistema de cache
│   ├── InstagramPostGenerator  # Generador de posts
│   └── InstagramAI         # Interfaz principal
│
├── config.py               # Configuraciones
│   ├── GenerationMode      # Enum: REFERENCE, CREATIVE, SCRATCH
│   ├── CompanyConfig       # Configuración de empresa
│   └── SystemConfig        # Configuración del sistema
│
├── prompts.py              # Prompts del sistema
│   ├── ANALYZE_REFERENCES_PROMPT   # Análisis de referencias
│   ├── ANALYZE_PRODUCT_BASIC_PROMPT    # Análisis básico de producto
│   ├── ANALYZE_PRODUCT_CONTEXT_PROMPT  # Análisis contextual
│   ├── ANALYZE_MESSAGE_PROMPT      # Análisis para modo scratch
│   ├── ANALYZE_POST_FOR_REGENERATION_PROMPT  # Análisis para regeneración
│   ├── get_reference_prompt()      # Prompt modo reference
│   ├── get_creative_prompt()       # Prompt modo creative
│   ├── get_scratch_prompt()        # Prompt modo scratch
│   └── get_regeneration_prompt()   # Prompt modo regeneración
│
├── referencias/            # Imágenes de referencia
│   ├── ref1.png
│   ├── ref2.png
│   └── ...
│
├── fotos/                  # Imágenes de productos
│   ├── producto1.png
│   └── ...
│
├── assets/                 # Assets de la empresa
│   └── logo.png
│
├── posts/                  # Carpeta de salida
│   ├── post_reference.png
│   ├── post_creative.png
│   └── post_scratch.png
│
├── .env                    # Variables de entorno
├── .gitignore             # Archivos ignorados
├── requirements.txt        # Dependencias
└── README.md              # Este archivo
```

---

## 📚 API Reference

### InstagramAI

#### `__init__(company, references_folder, config)`
Inicializa el sistema.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| company | CompanyConfig | Configuración de la empresa |
| references_folder | str | Carpeta con imágenes de referencia |
| config | SystemConfig | Configuración del sistema (opcional) |

---

#### `create_post(request, product_image, output, mode)`
Genera un post individual.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| request | str | Mensaje/solicitud del usuario |
| product_image | str | Ruta a imagen del producto (opcional) |
| output | str | Ruta de salida |
| mode | str | "reference" o "creative" |

**Retorna**: `Dict[str, Any]` con status y path

---

#### `create_scratch(request, output)`
Genera un post sin imagen de producto.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| request | str | Mensaje/solicitud del usuario |
| output | str | Ruta de salida |

**Retorna**: `Dict[str, Any]` con status y path

---

#### `create_both_versions(request, product_image, output_folder)`
Genera ambas versiones (reference y creative) de forma optimizada.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| request | str | Mensaje/solicitud del usuario |
| product_image | str | Ruta a imagen del producto |
| output_folder | str | Carpeta de salida |

**Retorna**: `Dict[str, Any]` con status de ambas versiones

---

#### `regenerate(existing_post, output, product_image, feedback)`
Regenera un post existente creando una versión mejorada.

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| existing_post | str | Ruta al post que se quiere regenerar |
| output | str | Ruta de salida para el nuevo post |
| feedback | str | Comentarios sobre qué mejorar (opcional) |

**Retorna**: `Dict[str, Any]` con status, path, mode y original

**Ejemplo**:
```python
result = ai.regenerate(
    existing_post="posts/post_creative.png",
    output="posts/post_v2.png",
    feedback="Quiero un fondo más limpio y el texto más grande"
)
```

---

#### `get_style_guide()`
Retorna el style guide extraído de las referencias.

**Retorna**: `str`

---

#### `clear_cache()`
Limpia el cache del style guide.

---

## 🔧 Solución de Problemas

### Error: "GEMINI_API_KEY not found"
```bash
# Verificar que existe .env con la key
cat .env
# Debe mostrar: GEMINI_API_KEY=tu-key
```

### Error: "No reference images found"
```bash
# Verificar que la carpeta referencias/ tiene imágenes
ls referencias/
# Debe mostrar: ref1.png, ref2.png, etc.
```

### Posts con logo duplicado
El sistema tiene reglas para evitar esto, pero si persiste:
```python
# Limpiar cache y regenerar
ai.clear_cache()
```

### Posts con marco/borde
El sistema está configurado para edge-to-edge. Si aparece marco, limpiar cache.

---

## 📝 Licencia

MIT License

---

## 🤝 Contribuciones

Pull requests son bienvenidos. Para cambios mayores, abrir un issue primero.

---

## 📞 Soporte

Para soporte o preguntas, crear un issue en el repositorio.
