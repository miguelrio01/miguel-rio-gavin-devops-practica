from uuid import uuid4


class Usuario:
    """Representa un usuario de la tienda."""

    def __init__(self, nombre: str, email: str) -> None:
        """Inicializa los datos comunes del usuario."""
        self.id: str = str(uuid4())
        self.nombre: str = nombre
        self.email: str = email

    def is_admin(self) -> bool:
        """Indica que el usuario base no es administrador."""
        return False


class Cliente(Usuario):
    """Representa un cliente con dirección postal."""

    def __init__(self, nombre: str, email: str, direccion: str) -> None:
        """Inicializa los datos del usuario y su dirección."""
        super().__init__(nombre, email)
        self.direccion: str = direccion


class Administrador(Usuario):
    """Representa un administrador de la tienda."""

    def is_admin(self) -> bool:
        """Indica que este usuario es administrador."""
        return True
