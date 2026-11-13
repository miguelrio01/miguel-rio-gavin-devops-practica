"""Esquemas de entrada y salida de usuarios."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class UsuarioCreate(BaseModel):
    """Datos necesarios para registrar un cliente o administrador."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=120)
    email: EmailStr
    tipo: Literal["cliente", "administrador"]
    direccion: str | None = Field(default=None, max_length=300)

    @field_validator("nombre", "direccion", mode="before")
    @classmethod
    def limpiar_texto(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor

    @model_validator(mode="after")
    def direccion_obligatoria_para_cliente(self) -> "UsuarioCreate":
        if self.tipo == "cliente" and not self.direccion:
            raise ValueError("Los clientes deben indicar una dirección postal.")
        return self


class UsuarioRead(BaseModel):
    """Información pública que devuelve la API de usuarios."""

    id: str
    nombre: str
    email: EmailStr
    es_admin: bool
