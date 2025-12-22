"""
Sistema de Programación de Posts de Instagram
Permite programar posts con fecha y hora, gestionar estados y simular publicación.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


# ============================================================================
# ESTADOS Y TIPOS
# ============================================================================

class PostStatus(Enum):
    """Estados posibles de un post programado"""
    DRAFT = "draft"                 # Borrador, aún no programado
    SCHEDULED = "scheduled"         # Programado, esperando fecha/hora
    GENERATING = "generating"       # En proceso de generación
    READY = "ready"                 # Generado y listo para publicar
    PUBLISHED = "published"         # Publicado (simulado)
    FAILED = "failed"               # Falló la generación
    CANCELLED = "cancelled"         # Cancelado


class PostType(Enum):
    """Tipos de posts disponibles"""
    SINGLE_CREATIVE = "single_creative"           # Un producto, modo creativo
    SINGLE_REFERENCE = "single_reference"         # Un producto, modo referencia
    SINGLE_BOTH = "single_both"                   # Un producto, ambas versiones
    SCRATCH = "scratch"                           # Sin producto
    MULTI_CREATIVE = "multi_creative"             # Multi-producto, modo creativo
    MULTI_REFERENCE = "multi_reference"           # Multi-producto, modo referencia
    MULTI_BOTH = "multi_both"                     # Multi-producto, ambas versiones
    EXISTING = "existing"                         # Post ya creado (solo programar)


# ============================================================================
# MODELO DE POST PROGRAMADO
# ============================================================================

@dataclass
class ScheduledPost:
    """Representa un post programado"""
    
    # Identificación
    id: str
    name: str                                     # Nombre descriptivo del post
    
    # Programación
    scheduled_datetime: Optional[datetime] = None # Fecha y hora de publicación
    status: PostStatus = PostStatus.DRAFT
    
    # Tipo de post
    post_type: PostType = PostType.SINGLE_CREATIVE
    
    # Configuración de generación (para posts nuevos)
    request: str = ""                             # Mensaje/solicitud del usuario
    product_images: List[str] = field(default_factory=list)  # Rutas de productos
    output_folder: str = "posts"
    
    # Rutas de imágenes generadas
    generated_paths: List[str] = field(default_factory=list)
    
    # Post existente (para tipo EXISTING)
    existing_image_path: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    
    # Resultado de generación
    generation_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        data = {
            "id": self.id,
            "name": self.name,
            "scheduled_datetime": self.scheduled_datetime.isoformat() if self.scheduled_datetime else None,
            "status": self.status.value,
            "post_type": self.post_type.value,
            "request": self.request,
            "product_images": self.product_images,
            "output_folder": self.output_folder,
            "generated_paths": self.generated_paths,
            "existing_image_path": self.existing_image_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "generation_result": self.generation_result,
            "error_message": self.error_message
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledPost":
        """Crea instancia desde diccionario"""
        return cls(
            id=data["id"],
            name=data["name"],
            scheduled_datetime=datetime.fromisoformat(data["scheduled_datetime"]) if data["scheduled_datetime"] else None,
            status=PostStatus(data["status"]),
            post_type=PostType(data["post_type"]),
            request=data.get("request", ""),
            product_images=data.get("product_images", []),
            output_folder=data.get("output_folder", "posts"),
            generated_paths=data.get("generated_paths", []),
            existing_image_path=data.get("existing_image_path"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None,
            generation_result=data.get("generation_result"),
            error_message=data.get("error_message")
        )


# ============================================================================
# GESTOR DE CALENDARIO
# ============================================================================

class PostScheduler:
    """
    Gestor de programación de posts de Instagram.
    
    Permite:
    - Crear y programar nuevos posts
    - Programar posts ya existentes
    - Gestionar estados
    - Simular publicación
    """
    
    def __init__(self, storage_file: str = ".scheduled_posts.json"):
        self.storage_file = Path(storage_file)
        self.posts: Dict[str, ScheduledPost] = {}
        self._load()
    
    # ========================================================================
    # PERSISTENCIA
    # ========================================================================
    
    def _load(self):
        """Carga posts desde archivo"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for post_data in data.get("posts", []):
                        post = ScheduledPost.from_dict(post_data)
                        self.posts[post.id] = post
                print(f"📅 {len(self.posts)} posts programados cargados")
            except Exception as e:
                print(f"⚠️ Error cargando posts: {e}")
                self.posts = {}
    
    def _save(self):
        """Guarda posts en archivo"""
        try:
            data = {
                "posts": [post.to_dict() for post in self.posts.values()],
                "updated_at": datetime.now().isoformat()
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error guardando posts: {e}")
    
    # ========================================================================
    # CREAR POSTS PARA PROGRAMAR
    # ========================================================================
    
    def create_single_post(
        self,
        name: str,
        request: str,
        product_image: Optional[str] = None,
        mode: Literal["creative", "reference", "both"] = "creative",
        scheduled_datetime: Optional[datetime] = None,
        output_folder: str = "posts"
    ) -> ScheduledPost:
        """
        Crea un post con un solo producto para programar.
        
        Args:
            name: Nombre descriptivo del post
            request: Mensaje/solicitud (ej: "20% de descuento en taladros")
            product_image: Ruta a la imagen del producto (opcional para scratch)
            mode: "creative", "reference" o "both"
            scheduled_datetime: Fecha y hora de publicación
            output_folder: Carpeta de salida
        
        Returns:
            ScheduledPost creado
        """
        # Determinar tipo de post
        if not product_image:
            post_type = PostType.SCRATCH
        elif mode == "both":
            post_type = PostType.SINGLE_BOTH
        elif mode == "reference":
            post_type = PostType.SINGLE_REFERENCE
        else:
            post_type = PostType.SINGLE_CREATIVE
        
        post = ScheduledPost(
            id=str(uuid.uuid4())[:8],
            name=name,
            scheduled_datetime=scheduled_datetime,
            status=PostStatus.SCHEDULED if scheduled_datetime else PostStatus.DRAFT,
            post_type=post_type,
            request=request,
            product_images=[product_image] if product_image else [],
            output_folder=output_folder
        )
        
        self.posts[post.id] = post
        self._save()
        
        status_msg = f"📅 Programado para {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}" if scheduled_datetime else "📝 Creado como borrador"
        print(f"\n✅ Post creado: {post.id}")
        print(f"   Nombre: {name}")
        print(f"   Tipo: {post_type.value}")
        print(f"   {status_msg}")
        
        return post
    
    def create_multi_product_post(
        self,
        name: str,
        request: str,
        product_images: List[str],
        mode: Literal["creative", "reference", "both"] = "creative",
        scheduled_datetime: Optional[datetime] = None,
        output_folder: str = "posts"
    ) -> ScheduledPost:
        """
        Crea un post con múltiples productos para programar.
        
        Args:
            name: Nombre descriptivo del post
            request: Mensaje/solicitud
            product_images: Lista de rutas a imágenes de productos (1-4)
            mode: "creative", "reference" o "both"
            scheduled_datetime: Fecha y hora de publicación
            output_folder: Carpeta de salida
        
        Returns:
            ScheduledPost creado
        """
        if len(product_images) < 1 or len(product_images) > 4:
            raise ValueError("Se requieren entre 1 y 4 productos")
        
        # Determinar tipo de post
        if mode == "both":
            post_type = PostType.MULTI_BOTH
        elif mode == "reference":
            post_type = PostType.MULTI_REFERENCE
        else:
            post_type = PostType.MULTI_CREATIVE
        
        post = ScheduledPost(
            id=str(uuid.uuid4())[:8],
            name=name,
            scheduled_datetime=scheduled_datetime,
            status=PostStatus.SCHEDULED if scheduled_datetime else PostStatus.DRAFT,
            post_type=post_type,
            request=request,
            product_images=product_images,
            output_folder=output_folder
        )
        
        self.posts[post.id] = post
        self._save()
        
        status_msg = f"📅 Programado para {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}" if scheduled_datetime else "📝 Creado como borrador"
        print(f"\n✅ Post multi-producto creado: {post.id}")
        print(f"   Nombre: {name}")
        print(f"   Productos: {len(product_images)}")
        print(f"   Tipo: {post_type.value}")
        print(f"   {status_msg}")
        
        return post
    
    def schedule_existing_post(
        self,
        name: str,
        image_path: str,
        scheduled_datetime: datetime
    ) -> ScheduledPost:
        """
        Programa un post ya creado/generado.
        
        Args:
            name: Nombre descriptivo del post
            image_path: Ruta a la imagen del post existente
            scheduled_datetime: Fecha y hora de publicación
        
        Returns:
            ScheduledPost creado
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Imagen no encontrada: {image_path}")
        
        post = ScheduledPost(
            id=str(uuid.uuid4())[:8],
            name=name,
            scheduled_datetime=scheduled_datetime,
            status=PostStatus.READY,  # Ya está listo porque la imagen existe
            post_type=PostType.EXISTING,
            existing_image_path=image_path,
            generated_paths=[image_path]
        )
        
        self.posts[post.id] = post
        self._save()
        
        print(f"\n✅ Post existente programado: {post.id}")
        print(f"   Nombre: {name}")
        print(f"   Imagen: {image_path}")
        print(f"   📅 Programado para: {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
        
        return post
    
    # ========================================================================
    # GESTIÓN DE POSTS
    # ========================================================================
    
    def get_post(self, post_id: str) -> Optional[ScheduledPost]:
        """Obtiene un post por ID"""
        return self.posts.get(post_id)
    
    def update_schedule(
        self,
        post_id: str,
        new_datetime: datetime
    ) -> Optional[ScheduledPost]:
        """
        Actualiza la fecha/hora de un post programado.
        
        Args:
            post_id: ID del post
            new_datetime: Nueva fecha y hora
        
        Returns:
            Post actualizado o None si no existe
        """
        post = self.posts.get(post_id)
        if not post:
            print(f"❌ Post no encontrado: {post_id}")
            return None
        
        if post.status == PostStatus.PUBLISHED:
            print(f"⚠️ No se puede reprogramar un post ya publicado")
            return None
        
        old_datetime = post.scheduled_datetime
        post.scheduled_datetime = new_datetime
        post.updated_at = datetime.now()
        
        # Actualizar estado si estaba en borrador
        if post.status == PostStatus.DRAFT:
            post.status = PostStatus.SCHEDULED
        
        self._save()
        
        old_str = old_datetime.strftime('%Y-%m-%d %H:%M') if old_datetime else "Sin fecha"
        print(f"\n✅ Post {post_id} reprogramado")
        print(f"   Antes: {old_str}")
        print(f"   Ahora: {new_datetime.strftime('%Y-%m-%d %H:%M')}")
        
        return post
    
    def cancel_post(self, post_id: str) -> Optional[ScheduledPost]:
        """
        Cancela un post programado.
        
        Args:
            post_id: ID del post
        
        Returns:
            Post cancelado o None si no existe
        """
        post = self.posts.get(post_id)
        if not post:
            print(f"❌ Post no encontrado: {post_id}")
            return None
        
        if post.status == PostStatus.PUBLISHED:
            print(f"⚠️ No se puede cancelar un post ya publicado")
            return None
        
        post.status = PostStatus.CANCELLED
        post.updated_at = datetime.now()
        self._save()
        
        print(f"\n✅ Post {post_id} cancelado")
        return post
    
    def delete_post(self, post_id: str) -> bool:
        """
        Elimina un post del calendario.
        
        Args:
            post_id: ID del post
        
        Returns:
            True si se eliminó, False si no existe
        """
        if post_id in self.posts:
            del self.posts[post_id]
            self._save()
            print(f"\n✅ Post {post_id} eliminado")
            return True
        
        print(f"❌ Post no encontrado: {post_id}")
        return False
    
    # ========================================================================
    # GENERACIÓN DE POSTS
    # ========================================================================
    
    def generate_post(self, post_id: str, ai_instance) -> Optional[ScheduledPost]:
        """
        Genera las imágenes de un post programado.
        
        Args:
            post_id: ID del post
            ai_instance: Instancia de InstagramAI para generar
        
        Returns:
            Post con imágenes generadas o None si falla
        """
        post = self.posts.get(post_id)
        if not post:
            print(f"❌ Post no encontrado: {post_id}")
            return None
        
        if post.post_type == PostType.EXISTING:
            print(f"⚠️ Post {post_id} ya tiene imagen, no requiere generación")
            return post
        
        if post.status == PostStatus.PUBLISHED:
            print(f"⚠️ Post {post_id} ya está publicado")
            return post
        
        print(f"\n🎨 Generando post: {post.name}")
        post.status = PostStatus.GENERATING
        post.updated_at = datetime.now()
        self._save()
        
        try:
            result = None
            
            # Generar según el tipo de post
            if post.post_type == PostType.SCRATCH:
                output_path = f"{post.output_folder}/scheduled_{post.id}_scratch.png"
                result = ai_instance.create_scratch(
                    request=post.request,
                    output=output_path
                )
                if result.get("status") == "success":
                    post.generated_paths = [result["path"]]
            
            elif post.post_type == PostType.SINGLE_CREATIVE:
                output_path = f"{post.output_folder}/scheduled_{post.id}_creative.png"
                result = ai_instance.create_post(
                    request=post.request,
                    product_image=post.product_images[0] if post.product_images else None,
                    output=output_path,
                    mode="creative"
                )
                if result.get("status") == "success":
                    post.generated_paths = [result["path"]]
            
            elif post.post_type == PostType.SINGLE_REFERENCE:
                output_path = f"{post.output_folder}/scheduled_{post.id}_reference.png"
                result = ai_instance.create_post(
                    request=post.request,
                    product_image=post.product_images[0] if post.product_images else None,
                    output=output_path,
                    mode="reference"
                )
                if result.get("status") == "success":
                    post.generated_paths = [result["path"]]
            
            elif post.post_type == PostType.SINGLE_BOTH:
                result = ai_instance.create_both_versions(
                    request=post.request,
                    product_image=post.product_images[0] if post.product_images else None,
                    output_folder=post.output_folder
                )
                paths = []
                if result.get("reference", {}).get("status") == "success":
                    paths.append(result["reference"]["path"])
                if result.get("creative", {}).get("status") == "success":
                    paths.append(result["creative"]["path"])
                post.generated_paths = paths
            
            elif post.post_type == PostType.MULTI_CREATIVE:
                output_path = f"{post.output_folder}/scheduled_{post.id}_multi_creative.png"
                result = ai_instance.create_multi_product(
                    request=post.request,
                    product_images=post.product_images,
                    output=output_path,
                    mode="creative"
                )
                if result.get("status") == "success":
                    post.generated_paths = [result["path"]]
            
            elif post.post_type == PostType.MULTI_REFERENCE:
                output_path = f"{post.output_folder}/scheduled_{post.id}_multi_reference.png"
                result = ai_instance.create_multi_product(
                    request=post.request,
                    product_images=post.product_images,
                    output=output_path,
                    mode="reference"
                )
                if result.get("status") == "success":
                    post.generated_paths = [result["path"]]
            
            elif post.post_type == PostType.MULTI_BOTH:
                result = ai_instance.create_multi_product_both_versions(
                    request=post.request,
                    product_images=post.product_images,
                    output_folder=post.output_folder
                )
                paths = []
                if result.get("reference", {}).get("status") == "success":
                    paths.append(result["reference"]["path"])
                if result.get("creative", {}).get("status") == "success":
                    paths.append(result["creative"]["path"])
                post.generated_paths = paths
            
            # Actualizar estado
            post.generation_result = result
            if post.generated_paths:
                post.status = PostStatus.READY
                print(f"\n✅ Post {post_id} generado exitosamente")
                print(f"   Imágenes: {post.generated_paths}")
            else:
                post.status = PostStatus.FAILED
                post.error_message = "No se generaron imágenes"
                print(f"\n❌ Post {post_id} falló en generación")
            
        except Exception as e:
            post.status = PostStatus.FAILED
            post.error_message = str(e)
            print(f"\n❌ Error generando post {post_id}: {e}")
        
        post.updated_at = datetime.now()
        self._save()
        return post
    
    # ========================================================================
    # SIMULACIÓN DE PUBLICACIÓN
    # ========================================================================
    
    def publish_post(self, post_id: str) -> Optional[ScheduledPost]:
        """
        Simula la publicación de un post (cambia estado a PUBLISHED).
        
        En el futuro, aquí se conectaría con la API de Instagram.
        
        Args:
            post_id: ID del post
        
        Returns:
            Post publicado o None si falla
        """
        post = self.posts.get(post_id)
        if not post:
            print(f"❌ Post no encontrado: {post_id}")
            return None
        
        # Verificar que esté listo para publicar
        if post.status not in [PostStatus.READY, PostStatus.SCHEDULED]:
            if post.status == PostStatus.PUBLISHED:
                print(f"⚠️ Post {post_id} ya está publicado")
            else:
                print(f"⚠️ Post {post_id} no está listo para publicar (estado: {post.status.value})")
            return None
        
        # Si no tiene imágenes generadas y no es EXISTING, no puede publicar
        if not post.generated_paths and post.post_type != PostType.EXISTING:
            print(f"⚠️ Post {post_id} no tiene imágenes generadas")
            return None
        
        # Simular publicación
        post.status = PostStatus.PUBLISHED
        post.published_at = datetime.now()
        post.updated_at = datetime.now()
        self._save()
        
        print(f"\n✅ Post {post_id} publicado (simulado)")
        print(f"   📅 Fecha publicación: {post.published_at.strftime('%Y-%m-%d %H:%M')}")
        if post.generated_paths:
            print(f"   📸 Imágenes: {post.generated_paths}")
        
        return post
    
    # ========================================================================
    # CONSULTAS Y LISTADOS
    # ========================================================================
    
    def get_pending_posts(self) -> List[ScheduledPost]:
        """
        Obtiene posts que deberían haberse publicado (fecha pasada y no publicados).
        
        Returns:
            Lista de posts pendientes ordenados por fecha
        """
        now = datetime.now()
        pending = []
        
        for post in self.posts.values():
            if (post.scheduled_datetime and 
                post.scheduled_datetime <= now and 
                post.status in [PostStatus.SCHEDULED, PostStatus.READY]):
                pending.append(post)
        
        return sorted(pending, key=lambda p: p.scheduled_datetime)
    
    def get_upcoming_posts(self, days: int = 7) -> List[ScheduledPost]:
        """
        Obtiene posts programados para los próximos N días.
        
        Args:
            days: Número de días a consultar
        
        Returns:
            Lista de posts ordenados por fecha
        """
        now = datetime.now()
        end_date = now + timedelta(days=days)
        upcoming = []
        
        for post in self.posts.values():
            if (post.scheduled_datetime and 
                now <= post.scheduled_datetime <= end_date and 
                post.status in [PostStatus.SCHEDULED, PostStatus.READY, PostStatus.DRAFT]):
                upcoming.append(post)
        
        return sorted(upcoming, key=lambda p: p.scheduled_datetime if p.scheduled_datetime else datetime.max)
    
    def list_all(self, status_filter: Optional[PostStatus] = None) -> List[ScheduledPost]:
        """
        Lista todos los posts, opcionalmente filtrados por estado.
        
        Args:
            status_filter: Estado para filtrar (opcional)
        
        Returns:
            Lista de posts ordenados por fecha de creación
        """
        posts = list(self.posts.values())
        
        if status_filter:
            posts = [p for p in posts if p.status == status_filter]
        
        return sorted(posts, key=lambda p: p.created_at, reverse=True)
    
    def print_calendar(self, days: int = 7):
        """
        Imprime el calendario de posts de forma visual.
        
        Args:
            days: Número de días a mostrar
        """
        print("\n" + "="*60)
        print(f"📅 CALENDARIO DE POSTS - Próximos {days} días")
        print("="*60)
        
        upcoming = self.get_upcoming_posts(days)
        
        if not upcoming:
            print("\n   No hay posts programados para este período")
        else:
            current_date = None
            for post in upcoming:
                if post.scheduled_datetime:
                    post_date = post.scheduled_datetime.date()
                    if post_date != current_date:
                        current_date = post_date
                        print(f"\n📆 {post_date.strftime('%A %d de %B, %Y')}")
                        print("-" * 40)
                    
                    status_emoji = {
                        PostStatus.DRAFT: "📝",
                        PostStatus.SCHEDULED: "⏰",
                        PostStatus.GENERATING: "🔄",
                        PostStatus.READY: "✅",
                        PostStatus.PUBLISHED: "📤",
                        PostStatus.FAILED: "❌",
                        PostStatus.CANCELLED: "🚫"
                    }
                    
                    emoji = status_emoji.get(post.status, "❓")
                    time_str = post.scheduled_datetime.strftime('%H:%M')
                    
                    print(f"   {time_str} | {emoji} {post.name[:30]}")
                    print(f"          └─ ID: {post.id} | Tipo: {post.post_type.value}")
        
        # Mostrar posts pendientes (fecha pasada)
        pending = self.get_pending_posts()
        if pending:
            print(f"\n⚠️ POSTS PENDIENTES ({len(pending)}):")
            print("-" * 40)
            for post in pending[:5]:  # Mostrar máximo 5
                time_str = post.scheduled_datetime.strftime('%Y-%m-%d %H:%M') if post.scheduled_datetime else "Sin fecha"
                print(f"   🔴 {post.name[:30]} | {time_str}")
        
        print("\n" + "="*60)
    
    def print_post_details(self, post_id: str):
        """
        Imprime los detalles completos de un post.
        
        Args:
            post_id: ID del post
        """
        post = self.posts.get(post_id)
        if not post:
            print(f"❌ Post no encontrado: {post_id}")
            return
        
        status_emoji = {
            PostStatus.DRAFT: "📝 Borrador",
            PostStatus.SCHEDULED: "⏰ Programado",
            PostStatus.GENERATING: "🔄 Generando",
            PostStatus.READY: "✅ Listo",
            PostStatus.PUBLISHED: "📤 Publicado",
            PostStatus.FAILED: "❌ Falló",
            PostStatus.CANCELLED: "🚫 Cancelado"
        }
        
        print("\n" + "="*60)
        print(f"📋 DETALLES DEL POST: {post.id}")
        print("="*60)
        print(f"   Nombre: {post.name}")
        print(f"   Estado: {status_emoji.get(post.status, post.status.value)}")
        print(f"   Tipo: {post.post_type.value}")
        
        if post.scheduled_datetime:
            print(f"   📅 Programado: {post.scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")
        
        if post.request:
            print(f"   📝 Mensaje: {post.request[:60]}...")
        
        if post.product_images:
            print(f"   📸 Productos: {len(post.product_images)}")
            for img in post.product_images:
                print(f"      - {img}")
        
        if post.generated_paths:
            print(f"   🖼️ Imágenes generadas:")
            for path in post.generated_paths:
                print(f"      - {path}")
        
        if post.existing_image_path:
            print(f"   🖼️ Imagen existente: {post.existing_image_path}")
        
        if post.published_at:
            print(f"   📤 Publicado: {post.published_at.strftime('%Y-%m-%d %H:%M')}")
        
        if post.error_message:
            print(f"   ⚠️ Error: {post.error_message}")
        
        print(f"\n   Creado: {post.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"   Actualizado: {post.updated_at.strftime('%Y-%m-%d %H:%M')}")
        print("="*60)


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def parse_datetime(date_str: str, time_str: str = "12:00") -> datetime:
    """
    Parsea una fecha y hora desde strings.
    
    Args:
        date_str: Fecha en formato "YYYY-MM-DD" o "DD/MM/YYYY"
        time_str: Hora en formato "HH:MM" (default: "12:00")
    
    Returns:
        datetime combinado
    
    Examples:
        parse_datetime("2024-12-25", "10:30")
        parse_datetime("25/12/2024", "14:00")
    """
    # Intentar diferentes formatos de fecha
    for date_fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
        try:
            date = datetime.strptime(date_str, date_fmt).date()
            break
        except ValueError:
            continue
    else:
        raise ValueError(f"Formato de fecha no reconocido: {date_str}")
    
    # Parsear hora
    try:
        time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        raise ValueError(f"Formato de hora no reconocido: {time_str}")
    
    return datetime.combine(date, time)


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Crear scheduler
    scheduler = PostScheduler()
    
    print("\n" + "="*60)
    print("📅 SISTEMA DE PROGRAMACIÓN DE POSTS")
    print("="*60)
    
    # ================================================================
    # EJEMPLO 1: Programar un post nuevo con producto
    # ================================================================
    # post1 = scheduler.create_single_post(
    #     name="Promoción Navidad - Taladros",
    #     request="¡Gran oferta navideña! 30% de descuento en taladros DeWalt",
    #     product_image="fotos/taladro.png",
    #     mode="both",  # Genera creative y reference
    #     scheduled_datetime=parse_datetime("2024-12-24", "10:00")
    # )
    
    # ================================================================
    # EJEMPLO 2: Programar un post scratch (sin producto)
    # ================================================================
    # post2 = scheduler.create_single_post(
    #     name="Aviso Año Nuevo",
    #     request="¡Feliz Año Nuevo! Estaremos cerrados del 31 al 2 de enero",
    #     product_image=None,  # Sin producto = scratch
    #     scheduled_datetime=parse_datetime("2025-12-22", "13:25")
    # )
    
    # ================================================================
    # EJEMPLO 3: Programar multi-producto
    # ================================================================
    # post3 = scheduler.create_multi_product_post(
    #     name="Combo Construcción",
    #     request="Todo para tu obra: cemento, varillas y blocks",
    #     product_images=["fotos/cemento.png", "fotos/varilla.png", "fotos/block.png"],
    #     mode="creative",
    #     scheduled_datetime=parse_datetime("2024-12-26", "09:00")
    # )
    
    # ================================================================
    # EJEMPLO 4: Programar un post ya existente
    # ================================================================
    # post4 = scheduler.schedule_existing_post(
    #     name="Post promocional existente",
    #     image_path="posts/post_creative.png",
    #     scheduled_datetime=parse_datetime("2024-12-25", "12:00")
    # )
    
    # ================================================================
    # VER CALENDARIO
    # ================================================================
    scheduler.print_calendar(days=14)
    
    # ================================================================
    # GENERAR UN POST (requiere instancia de InstagramAI)
    # ================================================================
    # from main import InstagramAI, CompanyConfig
    
    # company = CompanyConfig(
    #     name="Ferretería Gigante",
    #     description="Ferretería especializada en herramientas y construcción",
    #     color_palette=["#FF6B35", "#004E89", "#FFFFFF"],
    #     logo_path="assets/logo.png"
    # )
    # ai = InstagramAI(company, "referencias")
    
    # # Generar el post
    # scheduler.generate_post("e942fc28", ai)
    
    # ================================================================
    # SIMULAR PUBLICACIÓN
    # ================================================================
    # scheduler.publish_post("abc123")
    
    # ================================================================
    # OTRAS OPERACIONES
    # ================================================================
    # scheduler.update_schedule("abc123", parse_datetime("2024-12-27", "15:00"))
    # scheduler.cancel_post("abc123")
    # scheduler.delete_post("abc123")
    # scheduler.print_post_details("abc123")
    
    print("\n🎉 Sistema de programación listo!")

