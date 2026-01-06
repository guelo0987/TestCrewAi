from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from Dto.AuthDto import UserRegister, UserLogin, Token
from Services.auth_service import AuthService
from Utils.jwt_handler import get_current_user
from DbContext.database import get_db
from Models.Usuario import Usuario

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Endpoint para registrar un nuevo usuario"""
    return AuthService.register_user(user_data, db)


@router.post("/login", response_model=dict)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Endpoint para iniciar sesión usando JSON"""
    return AuthService.login_user(login_data, db)


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: Usuario = Depends(get_current_user)):
    """Endpoint para obtener información del usuario actual"""
    return {
        "id": str(current_user.id),
        "correo": current_user.correo,
        "nombre": current_user.nombre,
        "estado": current_user.estado,
        "ultimo_login": current_user.ultimo_login,
        "creado_en": current_user.creado_en
    }
