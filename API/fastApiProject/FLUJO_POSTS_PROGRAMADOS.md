# Flujo de Posts Programados

## 📋 Resumen

Un post programado es un post que se crea con una fecha y hora específica para su publicación futura. El sistema genera las imágenes inmediatamente, pero el post queda en estado `SCHEDULED` hasta que llegue la fecha programada.

---

## 🔄 Flujo Completo

### 1. **Creación del Post Programado**

#### Opción A: Crear post programado desde el inicio

**Endpoint:** `POST /posts/empresas/{empresa_id}/posts/producto`

**Parámetros en form-data:**
- `request_usuario`: Texto del post (ej: "20% de descuento en taladros")
- `imagen_producto`: Archivo de imagen del producto
- `nombre_interno`: (Opcional) Nombre para identificar el post
- `modo_estilo`: "creative" o "reference" (default: "creative")
- `generar_ambas_versiones`: true/false (default: false)
- `es_programado`: **true** ⭐
- `fecha_programada`: **"2024-01-20T09:00:00"** ⭐ (formato ISO)

**Ejemplo en Postman:**
```
POST /posts/empresas/{empresa_id}/posts/producto
Content-Type: multipart/form-data

Body (form-data):
- request_usuario: "Promoción especial en taladros"
- imagen_producto: [archivo]
- es_programado: true
- fecha_programada: "2024-01-20T09:00:00"
- generar_ambas_versiones: true
```

**Lo que sucede:**
1. ✅ La imagen del producto se sube a R2 en la carpeta `productos/` (permanente)
2. ✅ Se crea el registro del post en la base de datos con:
   - `es_programado = true`
   - `fecha_programada = "2024-01-20T09:00:00"`
   - `estado = SCHEDULED` (no DRAFT)
3. ✅ Se generan las versiones del post inmediatamente (reference y/o creative)
4. ✅ Las imágenes generadas se suben a R2 en la carpeta `posts/`
5. ✅ Se crean los registros de `VersionPost` con las URLs de las imágenes

**Estado inicial:** `SCHEDULED`

---

#### Opción B: Programar un post existente

**Endpoint:** `PUT /posts/empresas/{empresa_id}/posts/{post_id}/programar`

**Body (JSON):**
```json
{
  "fecha_programada": "2024-01-20T09:00:00"
}
```

**Lo que sucede:**
1. ✅ Se actualiza el post existente:
   - `es_programado = true`
   - `fecha_programada = "2024-01-20T09:00:00"`
   - `estado = SCHEDULED`

**Estado resultante:** `SCHEDULED`

---

### 2. **Estados del Post**

| Estado | Descripción | Cuándo se asigna |
|--------|-------------|------------------|
| `DRAFT` | Borrador, creado pero no finalizado | Cuando `es_programado=false` |
| `SCHEDULED` | Programado para publicación futura | Cuando `es_programado=true` |
| `READY` | Generado y listo para publicar | Manual o automático |
| `PUBLISHED` | Ya publicado | Después de publicar |
| `CANCELLED` | Cancelado | Si se cancela la programación |

---

### 3. **Gestión de Imágenes**

#### Imágenes de Producto:
- **Si `es_programado=true`**: Se guarda en `productos/` (permanente)
- **Si `es_programado=false`**: Se guarda en `temporal/` (puede limpiarse después)

#### Imágenes Generadas:
- Siempre se guardan en `posts/` con formato: `posts/post_{post_id}_v{version}_{variante}.png`
- Ejemplo: `posts/post_abc123_v1_reference.png`

---

### 4. **Flujo de Publicación (Pendiente de Implementar)**

⚠️ **IMPORTANTE:** Actualmente no hay un proceso automático que publique los posts cuando llegue la fecha programada.

**Flujo esperado (a implementar):**

1. **Worker/Scheduler** que ejecute periódicamente (ej: cada minuto):
   ```python
   # Pseudocódigo
   posts_programados = db.query(Post).filter(
       Post.estado == EstadoPost.SCHEDULED,
       Post.fecha_programada <= datetime.now(),
       Post.version_elegida_id.isnot(None)  # Debe tener versión elegida
   ).all()
   
   for post in posts_programados:
       # Publicar en Instagram (usando API de Instagram)
       publicar_en_instagram(post)
       
       # Actualizar estado
       post.estado = EstadoPost.PUBLISHED
       post.fecha_publicacion = datetime.now()
       db.commit()
   ```

2. **Requisitos antes de publicar:**
   - ✅ Post debe estar en estado `SCHEDULED`
   - ✅ `fecha_programada` debe ser <= ahora
   - ✅ Debe tener `version_elegida_id` (el usuario debe haber elegido una versión)

3. **Acción de publicación:**
   - Subir imagen a Instagram (usando Instagram Graph API)
   - Actualizar estado a `PUBLISHED`
   - Registrar `fecha_publicacion`

---

### 5. **Endpoints Relacionados**

#### Crear Post Programado:
```
POST /posts/empresas/{empresa_id}/posts/producto
POST /posts/empresas/{empresa_id}/posts/multi-producto
POST /posts/empresas/{empresa_id}/posts/scratch
```

#### Programar Post Existente:
```
PUT /posts/empresas/{empresa_id}/posts/{post_id}/programar
```

#### Ver Posts Programados:
```
GET /posts/empresas/{empresa_id}/posts?estado=SCHEDULED
```

#### Elegir Versión (requerido antes de publicar):
```
PUT /posts/empresas/{empresa_id}/posts/{post_id}/version
Body: { "version_id": "uuid-de-la-version" }
```

#### Actualizar Estado Manualmente:
```
PUT /posts/empresas/{empresa_id}/posts/{post_id}/estado
Body: { "estado": "READY" | "PUBLISHED" | "CANCELLED" }
```

---

### 6. **Ejemplo Completo de Flujo**

#### Paso 1: Crear Post Programado
```bash
POST /posts/empresas/{empresa_id}/posts/producto
{
  "request_usuario": "Promoción especial",
  "es_programado": true,
  "fecha_programada": "2024-01-20T09:00:00",
  "generar_ambas_versiones": true
}
```

**Respuesta:**
```json
{
  "status": "success",
  "post_id": "abc-123",
  "estado": "SCHEDULED",
  "fecha_programada": "2024-01-20T09:00:00",
  "reference": {
    "status": "success",
    "version_id": "ref-123",
    "imagen_url": "https://cdn.ferreteriagigante.com/posts/post_abc123_v1_reference.png"
  },
  "creative": {
    "status": "success",
    "version_id": "cre-123",
    "imagen_url": "https://cdn.ferreteriagigante.com/posts/post_abc123_v1_creative.png"
  }
}
```

#### Paso 2: Elegir Versión (Opcional, pero recomendado)
```bash
PUT /posts/empresas/{empresa_id}/posts/abc-123/version
{
  "version_id": "cre-123"
}
```

#### Paso 3: (Automático - Pendiente) Publicar cuando llegue la fecha
- El scheduler detecta que `fecha_programada <= ahora`
- Publica en Instagram
- Actualiza estado a `PUBLISHED`

---

## ⚠️ Notas Importantes

1. **Imágenes Permanentes**: Si `es_programado=true`, las imágenes se guardan permanentemente en `productos/` y `posts/`

2. **Versión Elegida**: Antes de publicar, el usuario debe elegir una versión usando el endpoint de selección

3. **Scheduler Pendiente**: Actualmente no hay proceso automático de publicación. Se debe implementar un worker/scheduler

4. **Formato de Fecha**: Usar formato ISO: `"2024-01-20T09:00:00"` o `"2024-01-20T09:00:00Z"`

5. **Validación**: El sistema valida que la empresa tenga colores de marca configurados antes de generar posts

---

## 🔧 Implementación Futura: Scheduler

Para implementar la publicación automática, se recomienda:

1. **Usar Celery + Redis** para tareas programadas
2. **Cron job** que ejecute cada minuto
3. **Instagram Graph API** para publicar posts
4. **Manejo de errores** y reintentos

Ejemplo de estructura:
```
/scheduler
  /tasks
    publish_scheduled_posts.py
  /workers
    instagram_publisher.py
```

