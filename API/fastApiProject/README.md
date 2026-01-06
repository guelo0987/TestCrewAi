# 📱 API de Generación de Posts de Instagram con IA

Sistema completo para generar posts de Instagram usando Gemini AI. El sistema aprende el estilo visual de tu marca analizando imágenes de referencia y genera posts consistentes con ese estilo.

## 📋 Tabla de Contenidos

1. [Concepto Principal](#concepto-principal)
2. [Requisitos Previos](#requisitos-previos)
3. [Instalación](#instalación)
4. [Variables de Entorno](#variables-de-entorno)
5. [Flujo Completo Paso a Paso](#flujo-completo-paso-a-paso)
6. [Endpoints de Autenticación](#endpoints-de-autenticación)
7. [Endpoints de Referencias (Carpeta de Estilos)](#endpoints-de-referencias)
8. [Endpoints de Cache (Style Guide)](#endpoints-de-cache)
9. [Endpoints de Posts](#endpoints-de-posts)
10. [Ejemplos Prácticos](#ejemplos-prácticos)

---

## 🎯 Concepto Principal

### ¿Cómo funciona?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUJO DE APRENDIZAJE DE ESTILO                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   📁 CARPETA DE REFERENCIAS              🤖 GEMINI ANALIZA                   │
│   ┌──────────────────────┐               ┌──────────────────┐               │
│   │  ref1.png            │               │                  │               │
│   │  ref2.png            │  ─────────▶   │  Style Guide     │               │
│   │  ref3.png            │    Analiza    │  (cache)         │               │
│   │  ...                 │    TODAS      │                  │               │
│   │  ref10.png           │    juntas     │                  │               │
│   └──────────────────────┘               └──────────────────┘               │
│                                                   │                          │
│                                                   ▼                          │
│                                          ┌──────────────────┐               │
│                                          │  POSTS GENERADOS │               │
│                                          │  con el mismo    │               │
│                                          │  estilo visual   │               │
│                                          └──────────────────┘               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ¿Qué son las referencias?

Las **referencias** son imágenes de posts existentes (tuyos o de inspiración) que definen el estilo visual que quieres para tu marca:

- 🎨 **Efectos de texto**: Outlines, sombras, tipografía
- 🏷️ **Tratamiento del logo**: Posición, tamaño, fondo
- 🖼️ **Estilo de fondo**: Colores, texturas, gradientes, diagonales
- 💰 **Elementos promocionales**: Cómo se muestran descuentos, precios, banners
- 🎯 **Layout**: Estructura, composición, jerarquía visual

**Recomendación**: Sube entre 5-15 imágenes de referencia con estilo CONSISTENTE.

---

## 🔧 Requisitos Previos

- Python 3.10+
- PostgreSQL 13+
- Cuenta de Google Cloud con API de Gemini habilitada
- Servicio de almacenamiento de imágenes (S3, GCS, Cloudinary, etc.)

## 📦 Instalación

```bash
cd API/fastApiProject
pip install -r requirements.txt
```

## 🔑 Variables de Entorno

Crea un archivo `.env` en `API/fastApiProject/`:

```env
# Base de datos PostgreSQL
DATABASE_URL=postgresql://usuario:password@localhost:5432/nombre_db

# JWT
SECRET_KEY=tu_clave_secreta_muy_larga_y_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Gemini AI
GEMINI_API_KEY=tu_api_key_de_gemini
```

## 🚀 Iniciar el Servidor

```bash
cd API/fastApiProject
uvicorn main:app --reload
```

- API: `http://localhost:8000`
- Documentación Swagger: `http://localhost:8000/docs`
- Documentación ReDoc: `http://localhost:8000/redoc`

---

## 🔄 Flujo Completo Paso a Paso

### Paso 1: Registro de Usuario y Empresa

```http
POST /auth/register
Content-Type: application/json

{
  "correo": "admin@ferreteria.com",
  "nombre": "Juan Admin",
  "password": "password123",
  "empresa": {
    "nombre": "Ferretería Gigante",
    "descripcion": "Ferretería especializada en herramientas y construcción",
    "logo_url": "https://tu-storage.com/logos/ferreteria-logo.png",
    "colores_marca": ["#FF6B35", "#004E89", "#FFFFFF"]
  }
}
```

**Respuesta:**
```json
{
  "message": "Usuario y empresa creados exitosamente",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "empresa_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

### Paso 2: Login para obtener Token

```http
POST /auth/login-json
Content-Type: application/json

{
  "correo": "admin@ferreteria.com",
  "password": "password123"
}
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

> ⚠️ **IMPORTANTE**: Guarda el `access_token`. Lo usarás en todas las siguientes peticiones como header:
> ```
> Authorization: Bearer {tu_token}
> ```

### Paso 3: Subir Carpeta de Referencias (Style Images)

Esta es la parte más importante. Sube tus imágenes de referencia que definen el estilo visual.

```http
POST /posts/empresas/{empresa_id}/referencias/batch
Authorization: Bearer {token}
Content-Type: application/json

{
  "imagenes_urls": [
    "https://tu-storage.com/referencias/post-ejemplo-1.png",
    "https://tu-storage.com/referencias/post-ejemplo-2.png",
    "https://tu-storage.com/referencias/post-ejemplo-3.png",
    "https://tu-storage.com/referencias/post-ejemplo-4.png",
    "https://tu-storage.com/referencias/post-ejemplo-5.png",
    "https://tu-storage.com/referencias/post-ejemplo-6.png",
    "https://tu-storage.com/referencias/post-ejemplo-7.png",
    "https://tu-storage.com/referencias/post-ejemplo-8.png",
    "https://tu-storage.com/referencias/post-ejemplo-9.png",
    "https://tu-storage.com/referencias/post-ejemplo-10.png"
  ],
  "reemplazar_existentes": false
}
```

**Respuesta:**
```json
{
  "total_creadas": 10,
  "referencias": [...],
  "mensaje": "Se crearon 10 referencias de estilo. Estas imágenes se analizarán juntas para extraer el estilo visual de tu empresa."
}
```

### Paso 4: Generar Style Guide (Opcional - Se hace automáticamente)

El style guide se genera automáticamente al crear el primer post. Pero puedes forzar su generación:

```http
POST /posts/empresas/{empresa_id}/cache/regenerar
Authorization: Bearer {token}
```

**Respuesta:**
```json
{
  "message": "Cache regenerado exitosamente",
  "style_guide_length": 4523
}
```

### Paso 5: Crear tu Primer Post

#### Opción A: Post con un Producto

```http
POST /posts/empresas/{empresa_id}/posts/producto
Authorization: Bearer {token}
Content-Type: application/json

{
  "request_usuario": "Promoción especial: Taladro DeWalt con 20% de descuento. Válido hasta el 31 de enero.",
  "nombre_interno": "Promo Taladro Enero 2024",
  "imagen_producto_url": "https://tu-storage.com/productos/taladro-dewalt.png",
  "modo_estilo": "creative",
  "generar_ambas_versiones": true
}
```

#### Opción B: Post con Múltiples Productos (1-4)

```http
POST /posts/empresas/{empresa_id}/posts/multi-producto
Authorization: Bearer {token}
Content-Type: application/json

{
  "request_usuario": "Todo para tu obra: Cemento, Varillas y Blocks disponibles",
  "nombre_interno": "Combo Construcción",
  "imagenes_productos_urls": [
    "https://tu-storage.com/productos/cemento.png",
    "https://tu-storage.com/productos/varillas.png",
    "https://tu-storage.com/productos/blocks.png"
  ],
  "modo_estilo": "creative",
  "generar_ambas_versiones": true
}
```

#### Opción C: Post sin Producto (Scratch)

```http
POST /posts/empresas/{empresa_id}/posts/scratch
Authorization: Bearer {token}
Content-Type: application/json

{
  "request_usuario": "¡Feliz Navidad! Les deseamos paz y prosperidad. Cerrado 24 y 25 de diciembre.",
  "nombre_interno": "Felicitación Navidad 2024"
}
```

### Paso 6: Iterar el Diseño

#### Si NO te gustó el diseño → REGENERAR (crear algo nuevo)

```http
POST /posts/empresas/{empresa_id}/posts/{post_id}/regenerar
Authorization: Bearer {token}
Content-Type: application/json

{
  "feedback": "El fondo está muy cargado, quiero algo más minimalista con más espacio blanco"
}
```

#### Si te gustó pero quieres ajustes → EDITAR (cambios puntuales)

```http
POST /posts/empresas/{empresa_id}/posts/{post_id}/editar
Authorization: Bearer {token}
Content-Type: application/json

{
  "cambios": "Mueve el logo a la esquina inferior derecha y haz el texto del precio más grande"
}
```

### Paso 7: Aprobar y Programar

```http
# Seleccionar la versión final
PUT /posts/empresas/{empresa_id}/posts/{post_id}/seleccionar-version
Authorization: Bearer {token}
Content-Type: application/json

{
  "version_id": "uuid-de-la-version-que-me-gusto"
}

# Aprobar para publicación
PUT /posts/empresas/{empresa_id}/posts/{post_id}/estado
Authorization: Bearer {token}
Content-Type: application/json

{
  "estado": "aprobado"
}

# Programar fecha de publicación
PUT /posts/empresas/{empresa_id}/posts/{post_id}/programar
Authorization: Bearer {token}
Content-Type: application/json

{
  "fecha_programada": "2024-01-20T09:00:00"
}
```

---

## 🔐 Endpoints de Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/auth/register` | Registrar usuario con empresa |
| POST | `/auth/login` | Login (form data) |
| POST | `/auth/login-json` | Login (JSON) |
| GET | `/auth/me` | Obtener usuario actual |

---

## 📁 Endpoints de Referencias (Carpeta de Estilos)

Las referencias son tu "carpeta" de imágenes de ejemplo. Todas se analizan juntas para extraer el estilo.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/posts/empresas/{id}/referencias` | Listar todas las referencias |
| POST | `/posts/empresas/{id}/referencias` | Agregar UNA referencia |
| POST | `/posts/empresas/{id}/referencias/batch` | **⭐ Subir MÚLTIPLES referencias (como una carpeta)** |
| PUT | `/posts/empresas/{id}/referencias/{ref_id}` | Actualizar referencia |
| DELETE | `/posts/empresas/{id}/referencias/{ref_id}` | Eliminar referencia |

### Subir Carpeta de Referencias (BATCH)

```http
POST /posts/empresas/{empresa_id}/referencias/batch
Authorization: Bearer {token}
Content-Type: application/json

{
  "imagenes_urls": [
    "https://storage.com/ref1.png",
    "https://storage.com/ref2.png",
    "https://storage.com/ref3.png",
    "https://storage.com/ref4.png",
    "https://storage.com/ref5.png"
  ],
  "reemplazar_existentes": false
}
```

**Parámetros:**
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `imagenes_urls` | array | URLs de las imágenes (1-20) |
| `reemplazar_existentes` | bool | Si `true`, borra las anteriores. Si `false`, agrega a las existentes. |

---

## 💾 Endpoints de Cache (Style Guide)

El cache almacena el análisis de las referencias (style_guide). Se genera automáticamente pero puedes forzarlo.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/posts/empresas/{id}/cache` | Ver style guide actual |
| POST | `/posts/empresas/{id}/cache/regenerar` | Forzar regeneración del style guide |

**¿Cuándo regenerar el cache?**
- Después de agregar/modificar/eliminar referencias
- Si el estilo generado no es correcto
- Si quieres "refrescar" el análisis

---

## 📝 Endpoints de Posts

### Crear Posts

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/posts/empresas/{id}/posts/producto` | Post con 1 producto |
| POST | `/posts/empresas/{id}/posts/multi-producto` | Post con 1-4 productos |
| POST | `/posts/empresas/{id}/posts/scratch` | Post sin producto (anuncios, fechas, etc.) |

### Iterar Posts

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/posts/empresas/{id}/posts/{post_id}/regenerar` | Diseño completamente nuevo |
| POST | `/posts/empresas/{id}/posts/{post_id}/editar` | Cambios puntuales al diseño |

### Consultar Posts

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/posts/empresas/{id}/posts` | Listar posts (paginado) |
| GET | `/posts/empresas/{id}/posts/{post_id}` | Detalle con versiones |
| GET | `/posts/empresas/{id}/posts/{post_id}/versiones` | Solo versiones |

### Gestionar Posts

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| PUT | `/posts/empresas/{id}/posts/{post_id}/seleccionar-version` | Elegir versión final |
| PUT | `/posts/empresas/{id}/posts/{post_id}/estado` | Cambiar estado |
| PUT | `/posts/empresas/{id}/posts/{post_id}/programar` | Programar publicación |
| DELETE | `/posts/empresas/{id}/posts/{post_id}` | Eliminar post |

---

## 🎨 Modos de Generación

| Modo | Descripción | Cuándo usar |
|------|-------------|-------------|
| **CREATIVE** | Crea ambiente contextual creativo (splashes de pintura, chispas, efectos) | Posts más llamativos y dinámicos |
| **REFERENCE** | Copia exactamente el estilo de las referencias | Máxima consistencia con posts anteriores |
| **SCRATCH** | Sin producto, genera visual basado en el mensaje | Anuncios, horarios, felicitaciones |

---

## 📚 Ejemplos de Edición

```json
// Mover elementos
{ "cambios": "Pon el logo arriba a la izquierda" }
{ "cambios": "El producto ponlo más a la derecha" }
{ "cambios": "Centra el texto principal" }

// Cambiar colores
{ "cambios": "Cambia el fondo a azul oscuro" }
{ "cambios": "Pon el porcentaje en color rojo" }
{ "cambios": "Haz el fondo más claro" }

// Modificar texto
{ "cambios": "Cambia '20%' por '35%'" }
{ "cambios": "Haz el texto más grande" }
{ "cambios": "Quita la fecha de validez" }
{ "cambios": "Agrega 'Envío gratis' abajo" }

// Agregar/quitar elementos
{ "cambios": "Quita el efecto de sombra del texto" }
{ "cambios": "Agrega un borde naranja" }
```

---

## 📊 Estados de un Post

| Estado | Descripción |
|--------|-------------|
| `borrador` | Creado pero no finalizado |
| `pendiente` | Esperando aprobación |
| `aprobado` | Aprobado para publicar |
| `programado` | Programado para publicación futura |
| `publicado` | Ya publicado |
| `cancelado` | Cancelado |

---

## 🏗️ Estructura de Base de Datos

```
empresas
├── referencias_estilo (1:N) ─────────────┐
│   Múltiples imágenes que definen        │
│   el estilo visual (como una carpeta)   │
│                                          ▼
├── cache_empresas (1:1) ─────────────────┤
│   Style guide generado al analizar       │
│   TODAS las referencias juntas           │
│                                          │
└── posts (1:N) ──────────────────────────┘
    └── versiones_posts (1:N)
        v1 (original)
        v2 (regeneración)
        v3 (edición)
        ...
```

---

## ❓ FAQ

**¿Cuántas referencias debo subir?**
- Mínimo 3-5 para resultados básicos
- Óptimo 8-15 para mejores resultados
- Máximo 20 (configurable)

**¿Qué tipo de referencias usar?**
- Posts de Instagram de tu marca o similares
- Deben tener estilo CONSISTENTE entre ellas
- Incluye variedad: promociones, productos, anuncios

**¿Cuánto tarda en generar un post?**
- Primera vez (análisis de referencias): 30-60 segundos
- Siguientes posts (con cache): 15-30 segundos

**¿Cómo almaceno las imágenes generadas?**
- El servicio retorna paths placeholder
- Debes implementar tu propio storage (S3, GCS, Cloudinary)
- Modifica `post_service.py` para subir las imágenes

**¿Puedo cambiar las referencias después?**
- Sí, agrega/elimina referencias en cualquier momento
- Regenera el cache después: `POST /empresas/{id}/cache/regenerar`

---

## 🔗 Links Útiles

- [Documentación Swagger](/docs)
- [Documentación ReDoc](/redoc)
- [Google Gemini API](https://ai.google.dev/)

