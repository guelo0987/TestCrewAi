"""
Servicio para gestión de empresas
Contiene toda la lógica de negocio relacionada con empresas.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from Models import Empresa, ReferenciaEstilo, CacheEmpresa, MiembroEmpresa, Usuario
from Dto.EmpresaDto import EmpresaResponse, MiEmpresaCompletaResponse
from Dto.PostDto import ReferenciaEstiloResponse, CacheEmpresaResponse


class EmpresaService:
    """Servicio para gestionar empresas"""
    
    @staticmethod
    def get_user_empresa(db: Session, usuario: Usuario) -> Empresa:
        """
        Obtiene la empresa del usuario actual.
        Si el usuario tiene múltiples empresas, retorna la primera.
        
        Args:
            db: Sesión de base de datos
            usuario: Usuario actual
            
        Returns:
            Empresa asociada al usuario
            
        Raises:
            HTTPException: Si no se encuentra empresa asociada
        """
        miembro = db.query(MiembroEmpresa).filter(
            MiembroEmpresa.usuario_id == usuario.id
        ).first()
        
        if not miembro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró ninguna empresa asociada a tu cuenta"
            )
        
        empresa = db.query(Empresa).filter(Empresa.id == miembro.empresa_id).first()
        
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa no encontrada"
            )
        
        return empresa
    
    @staticmethod
    def get_empresa_info(db: Session, usuario: Usuario) -> EmpresaResponse:
        """
        Obtiene la información básica de la empresa del usuario.
        
        Args:
            db: Sesión de base de datos
            usuario: Usuario actual
            
        Returns:
            EmpresaResponse con los datos de la empresa
        """
        empresa = EmpresaService.get_user_empresa(db, usuario)
        return EmpresaResponse.model_validate(empresa)
    
    @staticmethod
    def get_empresa_referencias(
        db: Session, 
        usuario: Usuario
    ) -> List[ReferenciaEstiloResponse]:
        """
        Obtiene todas las referencias de estilo de la empresa del usuario.
        
        Args:
            db: Sesión de base de datos
            usuario: Usuario actual
            
        Returns:
            Lista de ReferenciaEstiloResponse ordenadas por fecha de creación (más recientes primero)
        """
        empresa = EmpresaService.get_user_empresa(db, usuario)
        
        referencias = db.query(ReferenciaEstilo).filter(
            ReferenciaEstilo.empresa_id == empresa.id
        ).order_by(ReferenciaEstilo.creado_en.desc()).all()
        
        return [ReferenciaEstiloResponse.model_validate(ref) for ref in referencias]
    
    @staticmethod
    def get_empresa_cache(
        db: Session, 
        usuario: Usuario
    ) -> CacheEmpresaResponse:
        """
        Obtiene el cache del style_guide de la empresa del usuario.
        
        Args:
            db: Sesión de base de datos
            usuario: Usuario actual
            
        Returns:
            CacheEmpresaResponse con el cache del style_guide
            
        Raises:
            HTTPException: Si no existe cache
        """
        empresa = EmpresaService.get_user_empresa(db, usuario)
        
        cache = db.query(CacheEmpresa).filter(
            CacheEmpresa.empresa_id == empresa.id
        ).first()
        
        if not cache:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cache no encontrado. Genera un post para crear el cache del style_guide."
            )
        
        return CacheEmpresaResponse.model_validate(cache)
    
    @staticmethod
    def get_empresa_completa(
        db: Session, 
        usuario: Usuario
    ) -> MiEmpresaCompletaResponse:
        """
        Obtiene toda la información de la empresa del usuario en un solo objeto:
        - Datos de la empresa
        - Referencias de estilo
        - Cache del style_guide (si existe)
        
        Args:
            db: Sesión de base de datos
            usuario: Usuario actual
            
        Returns:
            MiEmpresaCompletaResponse con toda la información
        """
        empresa = EmpresaService.get_user_empresa(db, usuario)
        
        # Obtener referencias
        referencias = db.query(ReferenciaEstilo).filter(
            ReferenciaEstilo.empresa_id == empresa.id
        ).order_by(ReferenciaEstilo.creado_en.desc()).all()
        
        # Obtener cache
        cache = db.query(CacheEmpresa).filter(
            CacheEmpresa.empresa_id == empresa.id
        ).first()
        
        return MiEmpresaCompletaResponse(
            empresa=EmpresaResponse.model_validate(empresa),
            referencias=[ReferenciaEstiloResponse.model_validate(ref) for ref in referencias],
            cache=CacheEmpresaResponse.model_validate(cache) if cache else None,
            total_referencias=len(referencias),
            tiene_cache=cache is not None
        )


# Instancia global del servicio
empresa_service = EmpresaService()

