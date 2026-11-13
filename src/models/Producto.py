from uuid import uuid4


class Producto:
    """Representa un producto del inventario."""

    def __init__(self, nombre: str, precio: float, stock: int) -> None:
        """Inicializa el producto con un identificador único."""
        if stock < 0:
            raise ValueError("El stock inicial no puede ser negativo.")
        self.id: str = str(uuid4())
        self.nombre: str = nombre
        self.precio: float = precio
        self.stock: int = stock

    def comprobar_stock(self, cantidad: int) -> bool:
        """Indica si hay unidades suficientes para la cantidad solicitada."""
        return cantidad > 0 and cantidad <= self.stock

    def actualizar_stock(self, cantidad: int) -> bool:
        """Suma o resta unidades sin permitir un stock negativo."""
        if self.stock + cantidad < 0:
            return False
        self.stock += cantidad
        return True

    def __str__(self) -> str:
        """Devuelve las características principales del producto."""
        return (
            f"ID: {self.id} | {self.nombre} | "
            f"Precio: {self.precio:.2f} € | Stock: {self.stock}"
        )


class ProductoElectronico(Producto):
    """Representa un producto electrónico con garantía."""

    def __init__(
        self, nombre: str, precio: float, stock: int, meses_garantia: int
    ) -> None:
        """Inicializa los datos comunes y la garantía."""
        super().__init__(nombre, precio, stock)
        self.meses_garantia: int = meses_garantia

    def __str__(self) -> str:
        """Añade los meses de garantía a la descripción."""
        return (
            f"{super().__str__()} | "
            f"Garantía: {self.meses_garantia} meses"
        )


class ProductoRopa(Producto):
    """Representa una prenda con talla y color."""

    def __init__(
        self, nombre: str, precio: float, stock: int,
        talla: str, color: str
    ) -> None:
        """Inicializa los datos comunes, la talla y el color."""
        super().__init__(nombre, precio, stock)
        self.talla: str = talla
        self.color: str = color

    def __str__(self) -> str:
        """Añade la talla y el color a la descripción."""
        return (
            f"{super().__str__()} | "
            f"Talla: {self.talla} | Color: {self.color}"
        )
