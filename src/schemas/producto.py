"""Esquemas de entrada y salida de productos."""

import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


TipoProducto = Literal["generico", "electronico", "ropa"]


class ProductoCreate(BaseModel):
    """La categoría determina qué atributos específicos son obligatorios."""

    model_config = ConfigDict(extra="forbid")

    tipo: TipoProducto
    nombre: str = Field(min_length=1, max_length=150)
    precio: float = Field(gt=0, allow_inf_nan=False)
    stock: int = Field(ge=0)
    meses_garantia: int | None = Field(default=None, ge=0)
    talla: str | None = Field(default=None, max_length=30)
    color: str | None = Field(default=None, max_length=60)

    @field_validator("tipo", mode="before")
    @classmethod
    def normalizar_tipo(cls, valor: object) -> object:
        if not isinstance(valor, str):
            return valor
        texto = unicodedata.normalize("NFKD", valor.strip().lower())
        return "".join(c for c in texto if not unicodedata.combining(c))

    @field_validator("nombre", "talla", "color", mode="before")
    @classmethod
    def limpiar_texto(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor

    @model_validator(mode="after")
    def comprobar_atributos_segun_tipo(self) -> "ProductoCreate":
        if self.tipo == "generico":
            if any(v is not None for v in (self.meses_garantia, self.talla, self.color)):
                raise ValueError("Un producto genérico no admite atributos de electrónica o ropa.")
        elif self.tipo == "electronico":
            if self.meses_garantia is None:
                raise ValueError("Un producto electrónico requiere meses_garantia.")
            if self.talla is not None or self.color is not None:
                raise ValueError("Un producto electrónico no puede tener talla ni color.")
        elif self.tipo == "ropa":
            if not self.talla or not self.color:
                raise ValueError("Un producto de ropa requiere talla y color.")
            if self.meses_garantia is not None:
                raise ValueError("Un producto de ropa no puede tener meses_garantia.")
        return self


class ProductoRead(BaseModel):
    """Información del inventario con los atributos propios del tipo."""

    id: str
    tipo: TipoProducto
    nombre: str
    precio: float
    stock: int
    meses_garantia: int | None = None
    talla: str | None = None
    color: str | None = None
