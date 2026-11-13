"""Aplicación de gestión de una tienda online mediante FastAPI."""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from models.Pedido import Pedido
from models.Producto import Producto, ProductoElectronico, ProductoRopa
from models.Usuario import Cliente, Usuario
from schemas import (
    PedidoCreate, PedidoItemRead, PedidoRead,
    ProductoCreate, ProductoRead, UsuarioCreate, UsuarioRead,
)
from Services.Tienda_service import TiendaService

app = FastAPI(
    title="Tienda online - API REST",
    description="Gestión de usuarios, productos y pedidos.",
    version="1.0.0",
)

# La interfaz utiliza los mismos endpoints REST que la documentación de FastAPI.
CARPETA_WEB = Path(__file__).resolve().parent / "web"
app.mount("/static", StaticFiles(directory=CARPETA_WEB), name="static")


@app.get("/", include_in_schema=False)
def mostrar_aplicacion() -> FileResponse:
    return FileResponse(CARPETA_WEB / "index.html")


# Almacenamiento en memoria: se pierde al reiniciar el servidor.
tienda = TiendaService()


def obtener_tienda() -> TiendaService:
    """Dependencia inyectable: permite probar endpoints aislando el inventario."""
    return tienda


def usuario_a_read(usuario: Usuario) -> UsuarioRead:
    return UsuarioRead(
        id=usuario.id, nombre=usuario.nombre,
        email=usuario.email, es_admin=usuario.is_admin(),
    )


def producto_a_read(producto: Producto) -> ProductoRead:
    if isinstance(producto, ProductoElectronico):
        tipo = "electronico"
    elif isinstance(producto, ProductoRopa):
        tipo = "ropa"
    else:
        tipo = "generico"
    return ProductoRead(
        id=producto.id,
        tipo=tipo,
        nombre=producto.nombre,
        precio=producto.precio,
        stock=producto.stock,
        meses_garantia=getattr(producto, "meses_garantia", None),
        talla=getattr(producto, "talla", None),
        color=getattr(producto, "color", None),
    )


def pedido_a_read(pedido: Pedido) -> PedidoRead:
    return PedidoRead(
        id=pedido.id,
        fecha=pedido.fecha,
        cliente_id=pedido.cliente.id,
        cliente=usuario_a_read(pedido.cliente),
        total=round(pedido.calcular_total(), 2),
        items=[
            PedidoItemRead(
                producto_id=producto.id,
                nombre_producto=producto.nombre,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=round(producto.precio * cantidad, 2),
            )
            for producto, cantidad in pedido.productos
        ],
    )


def buscar_cliente(cliente_id: str, servicio: TiendaService) -> Cliente:
    usuario = servicio.usuarios.get(cliente_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="El usuario no existe.")
    if not isinstance(usuario, Cliente):
        raise HTTPException(status_code=403, detail="Solo los clientes pueden realizar o consultar pedidos.")
    return usuario


# ------------------------------ Usuarios ------------------------------
@app.post("/usuarios", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED, tags=["Usuarios"])
def crear_usuario(datos: UsuarioCreate, servicio: TiendaService = Depends(obtener_tienda)) -> UsuarioRead:
    if any(u.email.lower() == datos.email.lower() for u in servicio.usuarios.values()):
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email.")

    usuario = servicio.registrar_usuario(
        tipo=datos.tipo, nombre=datos.nombre,
        email=str(datos.email), direccion=datos.direccion or "",
    )
    if usuario is None:
        raise HTTPException(status_code=400, detail="No se ha podido registrar el usuario.")
    return usuario_a_read(usuario)


@app.get("/usuarios", response_model=list[UsuarioRead], tags=["Usuarios"])
def listar_usuarios(servicio: TiendaService = Depends(obtener_tienda)) -> list[UsuarioRead]:
    return [usuario_a_read(usuario) for usuario in servicio.usuarios.values()]


@app.get("/usuarios/{usuario_id}", response_model=UsuarioRead, tags=["Usuarios"])
def obtener_usuario(usuario_id: str, servicio: TiendaService = Depends(obtener_tienda)) -> UsuarioRead:
    usuario = servicio.usuarios.get(usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="El usuario no existe.")
    return usuario_a_read(usuario)


# ------------------------------ Productos -----------------------------
@app.post("/productos", response_model=ProductoRead, status_code=status.HTTP_201_CREATED, tags=["Productos"])
def crear_producto(datos: ProductoCreate, servicio: TiendaService = Depends(obtener_tienda)) -> ProductoRead:
    if datos.tipo == "electronico":
        producto = ProductoElectronico(datos.nombre, datos.precio, datos.stock, datos.meses_garantia)
    elif datos.tipo == "ropa":
        producto = ProductoRopa(datos.nombre, datos.precio, datos.stock, datos.talla, datos.color)
    else:
        producto = Producto(datos.nombre, datos.precio, datos.stock)
    servicio.añadir_producto(producto)
    return producto_a_read(producto)


@app.get("/productos", response_model=list[ProductoRead], tags=["Productos"])
def listar_productos(servicio: TiendaService = Depends(obtener_tienda)) -> list[ProductoRead]:
    return [producto_a_read(producto) for producto in servicio.productos.values()]


@app.get("/productos/{producto_id}", response_model=ProductoRead, tags=["Productos"])
def obtener_producto(producto_id: str, servicio: TiendaService = Depends(obtener_tienda)) -> ProductoRead:
    producto = servicio.productos.get(producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="El producto no existe.")
    return producto_a_read(producto)


@app.delete("/productos/{producto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Productos"])
def eliminar_producto(producto_id: str, servicio: TiendaService = Depends(obtener_tienda)) -> Response:
    if not servicio.eliminar_producto(producto_id):
        raise HTTPException(status_code=404, detail="El producto no existe.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------- Pedidos ------------------------------
@app.post("/pedidos", response_model=PedidoRead, status_code=status.HTTP_201_CREATED, tags=["Pedidos"])
def crear_pedido(datos: PedidoCreate, servicio: TiendaService = Depends(obtener_tienda)) -> PedidoRead:
    buscar_cliente(datos.cliente_id, servicio)

    cantidades = {item.producto_id: item.cantidad for item in datos.items}
    for producto_id, cantidad in cantidades.items():
        producto = servicio.productos.get(producto_id)
        if producto is None:
            raise HTTPException(status_code=404, detail=f"El producto {producto_id} no existe.")
        if not producto.comprobar_stock(cantidad):
            raise HTTPException(status_code=409, detail=f"Stock insuficiente para {producto.nombre}.")

    # TiendaService valida el pedido completo y actualiza el stock de modo atómico.
    pedido = servicio.realizar_pedido(datos.cliente_id, cantidades)
    if pedido is None:
        raise HTTPException(status_code=409, detail="No se ha podido completar el pedido.")
    return pedido_a_read(pedido)


@app.get("/usuarios/{cliente_id}/pedidos", response_model=list[PedidoRead], tags=["Pedidos"])
def listar_pedidos_cliente(cliente_id: str, servicio: TiendaService = Depends(obtener_tienda)) -> list[PedidoRead]:
    buscar_cliente(cliente_id, servicio)
    return [pedido_a_read(pedido) for pedido in servicio.listar_pedidos_usuario(cliente_id)]


if __name__ == "__main__":
    from iniciar import iniciar_servidor

    iniciar_servidor()
