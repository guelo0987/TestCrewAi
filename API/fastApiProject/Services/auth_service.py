from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from Models.Usuario import Usuario
from Models.Empresa import Empresa
from Models.Rol import Rol
from Models.MiembroEmpresa import MiembroEmpresa
from Models.ReferenciaEstilo import ReferenciaEstilo
from Dto.AuthDto import UserRegister, UserLogin
from Utils.jwt_handler import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from Utils.r2_storage import list_images_in_folder
from datetime import timedelta, datetime


class AuthService:
    @staticmethod
    def register_user(user_data: UserRegister, db: Session) -> dict:
        """Registra un nuevo usuario y crea su empresa con los datos proporcionados"""
        # Verificar si el correo ya existe
        existing_user = db.query(Usuario).filter(Usuario.correo == user_data.correo).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está registrado"
            )
        
        # Verificar si el nombre de usuario ya existe (opcional, dependiendo de tus reglas de negocio)
        existing_nombre = db.query(Usuario).filter(Usuario.nombre == user_data.nombre).first()
        if existing_nombre:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre ya está en uso"
            )
        
        # Verificar si el nombre de la empresa ya existe
        existing_empresa = db.query(Empresa).filter(Empresa.nombre == user_data.empresa.nombre).first()
        if existing_empresa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de la empresa ya está en uso"
            )
        
        # Crear el usuario con la contraseña hasheada
        password_hash = get_password_hash(user_data.password)
        new_usuario = Usuario(
            nombre=user_data.nombre,
            correo=user_data.correo,
            password_hash=password_hash,
            estado="activo"
        )
        
        # Guardar el usuario en la base de datos
        db.add(new_usuario)
        db.flush()  # Para obtener el ID del usuario sin hacer commit
        
        # Crear la empresa con los datos proporcionados por el usuario
        nueva_empresa = Empresa(
            nombre=user_data.empresa.nombre,
            descripcion=user_data.empresa.descripcion,
            logo_url=user_data.empresa.logo_url,
            colores_marca=user_data.empresa.colores_marca
        )
        db.add(nueva_empresa)
        db.flush()  # Para obtener el ID de la empresa sin hacer commit
        
        # Buscar el rol "cliente" (crear si no existe)
        rol_cliente = db.query(Rol).filter(Rol.nombre == "cliente").first()
        if not rol_cliente:
            # Si no existe, crear el rol "cliente"
            rol_cliente = Rol(nombre="cliente")
            db.add(rol_cliente)
            db.flush()
        
        # Crear la relación en miembros_empresa con rol "cliente"
        nuevo_miembro = MiembroEmpresa(
            empresa_id=nueva_empresa.id,
            usuario_id=new_usuario.id,
            rol_id=rol_cliente.id
        )
        db.add(nuevo_miembro)
        
        # Cargar referencias por defecto desde R2
        # Las referencias se cargan desde la carpeta "referencias/" en R2
        try:
            referencias_urls = list_images_in_folder("referencias/")
            
            if referencias_urls:
                # Crear referencia con todas las URLs encontradas
                nueva_referencia = ReferenciaEstilo(
                    empresa_id=nueva_empresa.id,
                    imagenes_urls=referencias_urls
                )
                db.add(nueva_referencia)
        except Exception as e:
            # Si falla la carga de referencias, continuar sin ellas
            # (no es crítico para el registro)
            print(f"⚠️  Advertencia: No se pudieron cargar las referencias por defecto: {str(e)}")
        
        # Hacer commit de todos los cambios
        db.commit()
        db.refresh(new_usuario)
        db.refresh(nueva_empresa)
        
        return {
            "message": "Usuario y empresa registrados exitosamente",
            "user": {
                "correo": new_usuario.correo,
                "nombre": new_usuario.nombre,
                "id": str(new_usuario.id)
            },
            "empresa": {
                "id": str(nueva_empresa.id),
                "nombre": nueva_empresa.nombre,
                "descripcion": nueva_empresa.descripcion,
                "logo_url": nueva_empresa.logo_url,
                "colores_marca": nueva_empresa.colores_marca
            },
            "rol": rol_cliente.nombre
        }
    
    @staticmethod
    def login_user(login_data: UserLogin, db: Session) -> dict:
        """Autentica un usuario y genera un token JWT"""
        # Buscar el usuario por correo
        usuario = db.query(Usuario).filter(Usuario.correo == login_data.correo).first()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar la contraseña
        if not verify_password(login_data.password, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar si el usuario está activo
        if usuario.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        # Actualizar último login
        usuario.ultimo_login = datetime.utcnow()
        db.commit()
        
        # Crear el token de acceso
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": usuario.correo},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "correo": usuario.correo,
                "nombre": usuario.nombre,
                "id": str(usuario.id)
            }
        }
    
    @staticmethod
    def get_user_by_email(correo: str, db: Session) -> Usuario:
        """Obtiene un usuario por correo"""
        return db.query(Usuario).filter(Usuario.correo == correo).first()
