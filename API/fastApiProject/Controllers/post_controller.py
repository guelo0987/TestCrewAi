"""
Controller para el sistema de generación de posts
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from DbContext.database import get_db
from Models import Empresa, Post, VersionPost, Usuario
from Dto.PostDto import (
    PostCreateProducto,
    PostCreateMultiProducto,
    PostCreateScratch,
    PostEditRequest,
    PostRegenerateRequest,
    PostResponse,
    PostResponseWithVersions,
    PostListResponse,
    PostUpdateEstado,
    PostSelectVersion,
    PostSchedule,
    VersionPostResponse,
    ModoEstiloEnum
)
from Services.post_service import post_service
from Services.image_service import ImageService
from Utils.jwt_handler import get_current_user
# Ya no se usa upload_image_to_r2 para imágenes de usuario

router = APIRouter(prefix="/posts", tags=["Posts"])


# ============================================================================
# HELPERS
# ============================================================================

def get_empresa_or_404(db: Session, empresa_id: UUID) -> Empresa:
    """Obtiene una empresa o lanza 404"""
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    return empresa


def get_post_or_404(db: Session, post_id: UUID, empresa_id: UUID) -> Post:
    """Obtiene un post o lanza 404"""
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.empresa_id == empresa_id
    ).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post no encontrado"
        )
    return post


# ============================================================================
# CACHE / STYLE GUIDE
# ============================================================================

@router.post("/empresas/{empresa_id}/cache/regenerar")
async def regenerar_cache(
    empresa_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Fuerza la regeneración del style_guide (invalida el cache)"""
    empresa = get_empresa_or_404(db, empresa_id)
    
    # Eliminar cache existente
    from Models import CacheEmpresa
    cache = db.query(CacheEmpresa).filter(CacheEmpresa.empresa_id == empresa_id).first()
    if cache:
        db.delete(cache)
        db.commit()
    
    # Regenerar
    style_guide = await post_service.get_or_create_style_guide(db, empresa)
    
    return {
        "message": "Cache regenerado exitosamente",
        "style_guide_length": len(style_guide)
    }


# ============================================================================
# CREAR POSTS
# ============================================================================

@router.post("/empresas/{empresa_id}/posts/producto")
async def crear_post_producto(
    empresa_id: UUID,
    request_usuario: str = Form(...),
    imagen_producto: UploadFile = File(...),
    nombre_interno: Optional[str] = Form(None),
    modo_estilo: str = Form("creative"),
    generar_ambas_versiones: bool = Form(False),
    es_programado: bool = Form(False),
    fecha_programada: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un post con un producto único.
    
    IMPORTANTE: La imagen del producto NO se guarda en R2 ni en la BD.
    Se usa temporalmente en memoria para generar el post inmediatamente.
    Solo se guardan las imágenes GENERADAS del post en R2 (carpeta posts/).
    
    El post se genera inmediatamente y luego puede programarse para publicación futura.
    
    Modos disponibles:
    - **creative**: Genera un ambiente contextual creativo
    - **reference**: Copia exacta del estilo de referencias
    
    Si `generar_ambas_versiones=True`, genera ambas versiones.
    """
    empresa = get_empresa_or_404(db, empresa_id)
    
    # Cargar imagen del producto directamente en memoria (NO se guarda en R2)
    product_image = ImageService.load_image_from_upload_file(imagen_producto)
    
    if not product_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo cargar la imagen del producto. Verifica que sea un archivo de imagen válido."
        )
    
    # Convertir modo_estilo string a enum
    modo_enum = ModoEstiloEnum.CREATIVE
    if modo_estilo.lower() == "reference":
        modo_enum = ModoEstiloEnum.REFERENCE
    
    result = await post_service.create_post_with_product(
        db=db,
        empresa=empresa,
        user_id=current_user.id,
        request_usuario=request_usuario,
        imagen_producto=product_image,  # PIL Image en memoria
        modo=modo_enum,
        nombre_interno=nombre_interno,
        generar_ambas=generar_ambas_versiones,
        es_programado=es_programado,
        fecha_programada=fecha_programada
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("mensaje", "Error en la generación"))
    
    return result


@router.post("/empresas/{empresa_id}/posts/multi-producto")
async def crear_post_multi_producto(
    empresa_id: UUID,
    request_usuario: str = Form(...),
    imagenes_productos: List[UploadFile] = File(...),
    nombre_interno: Optional[str] = Form(None),
    modo_estilo: str = Form("creative"),
    generar_ambas_versiones: bool = Form(False),
    es_programado: bool = Form(False),
    fecha_programada: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un post con múltiples productos (1-4).
    
    IMPORTANTE: Las imágenes de productos NO se guardan en R2 ni en la BD.
    Se usan temporalmente en memoria para generar el post inmediatamente.
    Solo se guardan las imágenes GENERADAS del post en R2 (carpeta posts/).
    
    El post se genera inmediatamente y luego puede programarse para publicación futura.
    """
    if len(imagenes_productos) < 1 or len(imagenes_productos) > 4:
        raise HTTPException(
            status_code=400,
            detail="Se requieren entre 1 y 4 imágenes de productos"
        )
    
    empresa = get_empresa_or_404(db, empresa_id)
    
    # Cargar imágenes de productos directamente en memoria (NO se guardan en R2)
    product_images = []
    for imagen in imagenes_productos:
        img = ImageService.load_image_from_upload_file(imagen)
        if not img:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se pudo cargar una de las imágenes. Verifica que sean archivos de imagen válidos."
            )
        product_images.append(img)
    
    # Convertir modo_estilo string a enum
    modo_enum = ModoEstiloEnum.CREATIVE
    if modo_estilo.lower() == "reference":
        modo_enum = ModoEstiloEnum.REFERENCE
    
    result = await post_service.create_multi_product_post(
        db=db,
        empresa=empresa,
        user_id=current_user.id,
        request_usuario=request_usuario,
        imagenes_productos=product_images,  # Lista de PIL Images en memoria
        modo=modo_enum,
        nombre_interno=nombre_interno,
        generar_ambas=generar_ambas_versiones,
        es_programado=es_programado,
        fecha_programada=fecha_programada
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("mensaje", "Error en la generación"))
    
    return result


@router.post("/empresas/{empresa_id}/posts/scratch")
async def crear_post_scratch(
    empresa_id: UUID,
    datos: PostCreateScratch,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un post desde cero sin imagen de producto.
    
    Ideal para:
    - Anuncios de horarios
    - Días festivos
    - Cierres temporales
    - Celebraciones
    """
    empresa = get_empresa_or_404(db, empresa_id)
    
    result = await post_service.create_scratch_post(
        db=db,
        empresa=empresa,
        user_id=current_user.id,
        request_usuario=datos.request_usuario,
        nombre_interno=datos.nombre_interno
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("mensaje", "Error en la generación"))
    
    return result


# ============================================================================
# REGENERAR Y EDITAR POSTS
# ============================================================================

@router.post("/empresas/{empresa_id}/posts/{post_id}/regenerar")
async def regenerar_post(
    empresa_id: UUID,
    post_id: UUID,
    datos: Optional[PostRegenerateRequest] = Body(None),
    version_base_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Regenera un post creando un diseño completamente nuevo.
    
    Usar cuando el diseño no gustó y se quiere algo diferente.
    Opcionalmente especifica `version_base_id` para regenerar desde una versión específica.
    El feedback es completamente opcional - puedes enviar un body vacío o sin body.
    """
    empresa = get_empresa_or_404(db, empresa_id)
    post = get_post_or_404(db, post_id, empresa_id)
    
    # Si no se proporciona datos, usar feedback vacío
    feedback = datos.feedback if datos and datos.feedback else ""
    
    result = await post_service.regenerate_post(
        db=db,
        post=post,
        empresa=empresa,
        feedback=feedback,
        version_base_id=version_base_id
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("mensaje", "Error en la regeneración"))
    
    return result


@router.post("/empresas/{empresa_id}/posts/{post_id}/editar")
async def editar_post(
    empresa_id: UUID,
    post_id: UUID,
    datos: PostEditRequest,
    version_base_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Edita un post haciendo cambios específicos.
    
    A diferencia de regenerar, mantiene el diseño original y solo hace los cambios solicitados.
    
    Ejemplos de cambios:
    - "Mueve el logo a la esquina inferior derecha"
    - "Cambia el color del fondo a azul oscuro"
    - "Haz el texto del precio más grande"
    """
    empresa = get_empresa_or_404(db, empresa_id)
    post = get_post_or_404(db, post_id, empresa_id)
    
    result = await post_service.edit_post(
        db=db,
        post=post,
        empresa=empresa,
        cambios=datos.cambios,
        version_base_id=version_base_id
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("mensaje", "Error en la edición"))
    
    return result


# ============================================================================
# CONSULTAR POSTS
# ============================================================================

@router.get("/empresas/{empresa_id}/posts", response_model=PostListResponse)
async def listar_posts(
    empresa_id: UUID,
    pagina: int = 1,
    por_pagina: int = 20,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista los posts de una empresa con paginación"""
    empresa = get_empresa_or_404(db, empresa_id)
    
    skip = (pagina - 1) * por_pagina
    posts = post_service.get_empresa_posts(db, empresa_id, skip, por_pagina)
    total = post_service.count_empresa_posts(db, empresa_id)
    
    return PostListResponse(
        posts=[PostResponse.model_validate(p) for p in posts],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina
    )


@router.get("/empresas/{empresa_id}/posts/{post_id}", response_model=PostResponseWithVersions)
async def obtener_post(
    empresa_id: UUID,
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un post con todas sus versiones"""
    empresa = get_empresa_or_404(db, empresa_id)
    post = get_post_or_404(db, post_id, empresa_id)
    
    # Cargar versiones
    versiones = db.query(VersionPost).filter(
        VersionPost.post_id == post_id
    ).order_by(VersionPost.numero_version).all()
    
    response = PostResponseWithVersions.model_validate(post)
    response.versiones = [VersionPostResponse.model_validate(v) for v in versiones]
    
    if post.version_elegida_id:
        version_elegida = db.query(VersionPost).filter(
            VersionPost.id == post.version_elegida_id
        ).first()
        if version_elegida:
            response.version_elegida = VersionPostResponse.model_validate(version_elegida)
    
    return response


@router.get("/empresas/{empresa_id}/posts/{post_id}/versiones", response_model=List[VersionPostResponse])
async def listar_versiones(
    empresa_id: UUID,
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todas las versiones de un post"""
    empresa = get_empresa_or_404(db, empresa_id)
    post = get_post_or_404(db, post_id, empresa_id)
    
    versiones = db.query(VersionPost).filter(
        VersionPost.post_id == post_id
    ).order_by(VersionPost.numero_version).all()
    
    return versiones


# ============================================================================
# GESTIONAR POSTS
# ============================================================================

@router.put("/empresas/{empresa_id}/posts/{post_id}/seleccionar-version")
async def seleccionar_version(
    empresa_id: UUID,
    post_id: UUID,
    datos: PostSelectVersion,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Selecciona una versión como la elegida/aprobada"""
    empresa = get_empresa_or_404(db, empresa_id)
    post = get_post_or_404(db, post_id, empresa_id)
    
    success = post_service.select_version(db, post, datos.version_id)
    if not success:
        raise HTTPException(status_code=404, detail="Versión no encontrada")
    
    return {"message": "Versión seleccionada", "version_id": str(datos.version_id)}


@router.put("/empresas/{empresa_id}/posts/{post_id}/estado")
async def actualizar_estado(
    empresa_id: UUID,
    post_id: UUID,
    datos: PostUpdateEstado,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza el estado de un post"""
    from Models import EstadoPost
    
    empresa = get_empresa_or_404(db, empresa_id)
    post = get_post_or_404(db, post_id, empresa_id)
    
    post_service.update_post_estado(db, post, EstadoPost(datos.estado.value))
    
    return {"message": "Estado actualizado", "nuevo_estado": datos.estado.value}


@router.put("/empresas/{empresa_id}/posts/{post_id}/programar")
async def programar_post(
    empresa_id: UUID,
    post_id: UUID,
    datos: PostSchedule,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Programa un post para publicación futura"""
    from Models import EstadoPost
    
    empresa = get_empresa_or_404(db, empresa_id)
    post = get_post_or_404(db, post_id, empresa_id)
    
    post.fecha_programada = datos.fecha_programada
    post.es_programado = True
    post.estado = EstadoPost.SCHEDULED
    db.commit()
    
    return {
        "message": "Post programado",
        "fecha_programada": datos.fecha_programada.isoformat()
    }


@router.delete("/empresas/{empresa_id}/posts/{post_id}")
async def eliminar_post(
    empresa_id: UUID,
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un post y todas sus versiones"""
    empresa = get_empresa_or_404(db, empresa_id)
    post = get_post_or_404(db, post_id, empresa_id)
    
    db.delete(post)
    db.commit()
    
    return {"message": "Post eliminado"}

