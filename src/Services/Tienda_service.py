from models.Pedido import Pedido
from models.Producto import Producto
from models.Usuario import Administrador, Cliente, Usuario


class TiendaService:
    """Centraliza los usuarios, el inventario y los pedidos."""

    def __init__(self) -> None:
        """Crea las colecciones vacías de la tienda."""
        self.usuarios: dict[str, Usuario] = {}
        self.productos: dict[str, Producto] = {}
        self.pedidos: list[Pedido] = []

    def registrar_usuario(
        self, tipo: str, nombre: str, email: str, direccion: str = ""
    ) -> Usuario | None:
        """Crea y guarda un cliente o un administrador."""
        usuario: Usuario
        if tipo == "cliente":
            if not direccion.strip():
                print("El cliente necesita una dirección.")
                return None
            usuario = Cliente(nombre, email, direccion)
        elif tipo == "administrador":
            usuario = Administrador(nombre, email)
        else:
            print("Tipo de usuario no válido.")
            return None

        self.usuarios[usuario.id] = usuario
        return usuario

    def añadir_producto(self, producto: Producto) -> None:
        """Añade un producto de cualquier categoría al inventario."""
        self.productos[producto.id] = producto

    def eliminar_producto(self, id_producto: str) -> bool:
        """Elimina el producto si existe e indica el resultado."""
        if id_producto not in self.productos:
            print("El producto no existe.")
            return False
        del self.productos[id_producto]
        return True

    def listar_productos(self) -> None:
        """Muestra los productos utilizando su método __str__."""
        for producto in self.productos.values():
            print(producto)

    def realizar_pedido(
        self, id_usuario: str, cantidades: dict[str, int]
    ) -> Pedido | None:
        """Valida toda la compra antes de descontar el stock."""
        if id_usuario not in self.usuarios:
            print("El usuario no existe.")
            return None

        usuario = self.usuarios[id_usuario]
        if not isinstance(usuario, Cliente):
            print("Solo los clientes pueden realizar pedidos.")
            return None

        if not cantidades:
            print("El pedido debe contener productos.")
            return None

        productos_pedido: list[tuple[Producto, int]] = []

        # Primero se comprueban todos los productos y sus cantidades.
        for id_producto, cantidad in cantidades.items():
            if id_producto not in self.productos:
                print("Un producto del pedido no existe.")
                return None
            if type(cantidad) is not int or cantidad <= 0:
                print("Las cantidades deben ser enteros positivos.")
                return None

            producto = self.productos[id_producto]
            if not producto.comprobar_stock(cantidad):
                print(f"Stock insuficiente de {producto.nombre}.")
                return None
            productos_pedido.append((producto, cantidad))

        # Solo se modifica el inventario tras validar el pedido completo.
        pedido = Pedido(usuario, productos_pedido)
        for producto, cantidad in productos_pedido:
            producto.actualizar_stock(-cantidad)

        self.pedidos.append(pedido)
        return pedido

    def listar_pedidos_usuario(self, id_usuario: str) -> list[Pedido]:
        """Devuelve los pedidos del usuario del más antiguo al reciente."""
        pedidos_usuario: list[Pedido] = []
        for pedido in self.pedidos:
            if pedido.cliente.id == id_usuario:
                pedidos_usuario.append(pedido)
        return sorted(pedidos_usuario, key=lambda pedido: pedido.fecha)
