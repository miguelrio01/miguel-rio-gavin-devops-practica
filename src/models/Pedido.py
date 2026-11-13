from datetime import datetime
from uuid import uuid4

from models.Producto import Producto
from models.Usuario import Cliente


class Pedido:
    """Representa la compra de un cliente."""

    def __init__(
        self, cliente: Cliente, productos: list[tuple[Producto, int]]
    ) -> None:
        """Guarda el cliente, los productos y la fecha del pedido."""
        self.id: str = str(uuid4())
        self.cliente: Cliente = cliente
        self.productos: list[tuple[Producto, int]] = productos.copy()
        self.fecha: datetime = datetime.now()

    def calcular_total(self) -> float:
        """Suma el precio de cada producto multiplicado por su cantidad."""
        total: float = 0.0
        for producto, cantidad in self.productos:
            total += producto.precio * cantidad
        return total

    def __str__(self) -> str:
        """Devuelve un resumen del pedido."""
        return (
            f"Pedido: {self.id} | "
            f"Fecha: {self.fecha:%d/%m/%Y %H:%M:%S} | "
            f"Cliente: {self.cliente.nombre} | "
            f"Total: {self.calcular_total():.2f} €"
        )
