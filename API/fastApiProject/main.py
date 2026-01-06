from fastapi import FastAPI
from Controllers import auth_controller, post_controller, empresa_controller
from DbContext.database import engine, Base
from Models import (
    Usuario, 
    Empresa, 
    Rol, 
    MiembroEmpresa,
    ReferenciaEstilo,
    CacheEmpresa,
    Post,
    VersionPost
)

# Crear las tablas si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Generación de Posts",
    description="""
    API para generación de posts de Instagram con IA.
    
    ## Funcionalidades
    
    - **Autenticación**: Registro, login y gestión de usuarios
    - **Empresas**: Cada usuario pertenece a una empresa
    - **Referencias de Estilo**: Imágenes que definen el estilo visual
    - **Cache**: Style guide generado automáticamente
    - **Posts**: Generación de posts con múltiples modos
    - **Versiones**: Historial de versiones de cada post
    
    ## Modos de Generación
    
    - **CREATIVE**: Ambiente contextual creativo
    - **REFERENCE**: Copia exacta del estilo de referencias
    - **SCRATCH**: Sin imagen de producto, genera todo desde el mensaje
    
    ## Tipos de Contenido
    
    - **Producto Único**: Post con un solo producto
    - **Multi-Producto**: Post con 1-4 productos
    - **Scratch**: Sin producto, solo mensaje (anuncios, horarios, etc.)
    """,
    version="2.0.0"
)

# Incluir routers
app.include_router(auth_controller.router)
app.include_router(post_controller.router)
app.include_router(empresa_controller.router)


@app.get("/")
async def root():
    return {
        "message": "Bienvenido a la API de Generación de Posts",
        "version": "2.0.0",
        "endpoints": {
            "auth": {
                "register": "/auth/register",
                "login": "/auth/login",
                "login_json": "/auth/login-json",
                "me": "/auth/me"
            },
            "empresas": {
                "mi_empresa": "/empresas/mi-empresa",
                "mis_referencias": "/empresas/mi-empresa/referencias",
                "mi_cache": "/empresas/mi-empresa/cache",
                "completa": "/empresas/mi-empresa/completa",
                "refresh_referencias": "POST /empresas/mi-empresa/referencias/refresh"
            },
            "posts": {
                "regenerar_cache": "POST /posts/empresas/{empresa_id}/cache/regenerar",
                "crear_producto": "POST /posts/empresas/{empresa_id}/posts/producto",
                "crear_multi_producto": "POST /posts/empresas/{empresa_id}/posts/multi-producto",
                "crear_scratch": "POST /posts/empresas/{empresa_id}/posts/scratch",
                "regenerar": "POST /posts/empresas/{empresa_id}/posts/{post_id}/regenerar",
                "editar": "POST /posts/empresas/{empresa_id}/posts/{post_id}/editar",
                "listar": "GET /posts/empresas/{empresa_id}/posts",
                "detalle": "GET /posts/empresas/{empresa_id}/posts/{post_id}",
                "versiones": "GET /posts/empresas/{empresa_id}/posts/{post_id}/versiones",
                "seleccionar_version": "PUT /posts/empresas/{empresa_id}/posts/{post_id}/seleccionar-version",
                "actualizar_estado": "PUT /posts/empresas/{empresa_id}/posts/{post_id}/estado",
                "programar": "PUT /posts/empresas/{empresa_id}/posts/{post_id}/programar",
                "eliminar": "DELETE /posts/empresas/{empresa_id}/posts/{post_id}"
            }
        }
    }
