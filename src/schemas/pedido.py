"""Esquemas de entrada y salida de pedidos."""

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from .usuario import UsuarioRead


class PedidoItemCreate(BaseModel):
    """Un producto y una cantidad positiva dentro del nuevo pedido."""

    model_config = ConfigDict(extra="forbid")

    producto_id: str = Field(min_length=1, validation_alias=AliasChoices("producto_id", "id_producto"))
    cantidad: int = Field(gt=0)


class PedidoCreate(BaseModel):
    """Cliente y líneas de pedido (sin identificadores repetidos)."""

    model_config = ConfigDict(extra="forbid")

    cliente_id: str = Field(min_length=1, validation_alias=AliasChoices("cliente_id", "id_cliente"))
    items: list[PedidoItemCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def no_permitir_productos_duplicados(self) -> "PedidoCreate":
        ids = [item.producto_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Un producto no puede aparecer dos veces en el mismo pedido.")
        return self


class PedidoItemRead(BaseModel):
    """Detalle de una línea de pedido, incluidos sus importes."""

    producto_id: str
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    subtotal: float


class PedidoRead(BaseModel):
    """Pedido completo: fecha, cliente, total y productos adquiridos."""

    id: str
    fecha: datetime
    cliente_id: str
    cliente: UsuarioRead
    total: float
    items: list[PedidoItemRead]
