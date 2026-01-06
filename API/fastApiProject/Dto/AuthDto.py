from pydantic import BaseModel, EmailStr
from typing import Optional


class EmpresaRegister(BaseModel):
    """DTO para datos de la empresa al registrarse"""
    nombre: str
    descripcion: Optional[str] = None
    logo_url: Optional[str] = None
    colores_marca: Optional[dict] = None


class UserRegister(BaseModel):
    """DTO para registro de usuario con su empresa"""
    correo: EmailStr
    nombre: str
    password: str
    empresa: EmpresaRegister


class UserLogin(BaseModel):
    correo: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    correo: Optional[EmailStr] = None
