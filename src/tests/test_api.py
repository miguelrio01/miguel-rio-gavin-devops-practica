"""Pruebas funcionales de la API: endpoints, errores, stock y documentación."""

import pytest
from fastapi.testclient import TestClient

from main import app, obtener_tienda
from Services.Tienda_service import TiendaService


@pytest.fixture
def api():
    servicio = TiendaService()
    app.dependency_overrides[obtener_tienda] = lambda: servicio
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()


def crear_cliente(api, email="ana@example.com"):
    respuesta = api.post("/usuarios", json={
        "tipo": "cliente", "nombre": "Ana", "email": email,
        "direccion": "Calle Mayor, 1",
    })
    assert respuesta.status_code == 201
    return respuesta.json()


def crear_producto(api, **cambios):
    datos = {"tipo": "electronico", "nombre": "Portátil", "precio": 800, "stock": 5, "meses_garantia": 24}
    datos.update(cambios)
    respuesta = api.post("/productos", json=datos)
    assert respuesta.status_code == 201
    return respuesta.json()


def test_openapi_incluye_todas_las_rutas(api):
    respuesta = api.get("/openapi.json")
    assert respuesta.status_code == 200
    rutas = respuesta.json()["paths"]
    assert {"/usuarios", "/usuarios/{usuario_id}", "/productos", "/productos/{producto_id}",
            "/pedidos", "/usuarios/{cliente_id}/pedidos"} <= set(rutas)
    assert "post" in rutas["/usuarios"]
    assert "get" in rutas["/usuarios"]
    assert "delete" in rutas["/productos/{producto_id}"]


def test_usuarios_crear_listar_y_consultar(api):
    ana = crear_cliente(api)
    assert ana["es_admin"] is False
    admin = api.post("/usuarios", json={
        "tipo": "administrador", "nombre": "Carlos", "email": "carlos@example.com",
    })
    assert admin.status_code == 201
    assert admin.json()["es_admin"] is True
    assert len(api.get("/usuarios").json()) == 2
    assert api.get(f"/usuarios/{ana['id']}").json() == ana
    assert api.get("/usuarios/no-existe").status_code == 404


def test_usuario_valida_tipo_email_y_direccion(api):
    valido = {"tipo": "cliente", "nombre": "Ana", "email": "ana@example.com"}
    assert api.post("/usuarios", json=valido).status_code == 422
    assert api.post("/usuarios", json={**valido, "direccion": "  "}).status_code == 422
    assert api.post("/usuarios", json={**valido, "direccion": "Calle A", "email": "invalido"}).status_code == 422
    assert api.post("/usuarios", json={**valido, "direccion": "Calle A", "tipo": "otro"}).status_code == 422


def test_usuario_email_duplicado(api):
    crear_cliente(api)
    assert api.post("/usuarios", json={
        "tipo": "administrador", "nombre": "Otra", "email": "ana@example.com",
    }).status_code == 409


def test_productos_tres_tipos_y_listado(api):
    generico = crear_producto(api, tipo="generico", nombre="Caja", meses_garantia=None)
    electronico = crear_producto(api)
    ropa = crear_producto(api, tipo="ropa", meses_garantia=None, talla="M", color="Azul")
    assert generico["tipo"] == "generico"
    assert generico["meses_garantia"] is None
    assert electronico["meses_garantia"] == 24
    assert ropa["talla"] == "M" and ropa["color"] == "Azul"
    assert len(api.get("/productos").json()) == 3
    assert api.get(f"/productos/{ropa['id']}").json() == ropa


def test_producto_acepta_tipos_con_tilde(api):
    respuesta = api.post("/productos", json={
        "tipo": "electrónico", "nombre": "Teclado", "precio": 20, "stock": 3,
        "meses_garantia": 12,
    })
    assert respuesta.status_code == 201
    assert respuesta.json()["tipo"] == "electronico"


@pytest.mark.parametrize("datos", [
    {"tipo": "electronico", "nombre": "Móvil", "precio": 50, "stock": 1},
    {"tipo": "ropa", "nombre": "Camisa", "precio": 20, "stock": 2, "talla": "M"},
    {"tipo": "generico", "nombre": "Caja", "precio": -1, "stock": 2},
    {"tipo": "generico", "nombre": "Caja", "precio": 2, "stock": -1},
    {"tipo": "generico", "nombre": "Caja", "precio": 2, "stock": 1, "color": "Rojo"},
    {"tipo": "ropa", "nombre": "Camisa", "precio": 2, "stock": 1, "talla": " ", "color": "Azul"},
    {"tipo": "otro", "nombre": "X", "precio": 1, "stock": 1},
])
def test_productos_invalidos(api, datos):
    assert api.post("/productos", json=datos).status_code == 422


def test_eliminar_producto(api):
    producto = crear_producto(api)
    assert api.delete(f"/productos/{producto['id']}").status_code == 204
    assert api.get(f"/productos/{producto['id']}").status_code == 404
    assert api.delete(f"/productos/{producto['id']}").status_code == 404


def test_pedido_crea_historico_y_descuenta_stock(api):
    cliente = crear_cliente(api)
    portatil = crear_producto(api)
    camiseta = crear_producto(api, tipo="ropa", nombre="Camiseta", precio=20,
                             stock=10, meses_garantia=None, talla="M", color="Azul")
    pedido = api.post("/pedidos", json={
        "cliente_id": cliente["id"],
        "items": [{"producto_id": portatil["id"], "cantidad": 1},
                  {"producto_id": camiseta["id"], "cantidad": 2}],
    })
    assert pedido.status_code == 201
    datos = pedido.json()
    assert datos["total"] == 840.0
    assert datos["fecha"]
    assert datos["cliente"]["id"] == cliente["id"]
    assert len(datos["items"]) == 2
    assert datos["items"][1]["subtotal"] == 40.0
    assert api.get(f"/productos/{portatil['id']}").json()["stock"] == 4
    assert api.get(f"/productos/{camiseta['id']}").json()["stock"] == 8
    assert api.get(f"/usuarios/{cliente['id']}/pedidos").json() == [datos]


def test_pedido_con_stock_insuficiente_no_modifica_ningun_producto(api):
    cliente = crear_cliente(api)
    producto1 = crear_producto(api)
    producto2 = crear_producto(api, nombre="Monitor", stock=1)
    respuesta = api.post("/pedidos", json={
        "cliente_id": cliente["id"],
        "items": [{"producto_id": producto1["id"], "cantidad": 3},
                  {"producto_id": producto2["id"], "cantidad": 4}],
    })
    assert respuesta.status_code == 409
    assert api.get(f"/productos/{producto1['id']}").json()["stock"] == 5
    assert api.get(f"/productos/{producto2['id']}").json()["stock"] == 1
    assert api.get(f"/usuarios/{cliente['id']}/pedidos").json() == []


def test_pedido_producto_inexistente_no_descuenta_stock(api):
    cliente = crear_cliente(api)
    producto = crear_producto(api)
    respuesta = api.post("/pedidos", json={
        "cliente_id": cliente["id"],
        "items": [{"producto_id": producto["id"], "cantidad": 1},
                  {"producto_id": "inexistente", "cantidad": 1}],
    })
    assert respuesta.status_code == 404
    assert api.get(f"/productos/{producto['id']}").json()["stock"] == 5


def test_pedido_cliente_inexistente_y_admin(api):
    prod = crear_producto(api)
    assert api.post("/pedidos", json={"cliente_id": "inexistente", "items": [{
        "producto_id": prod["id"], "cantidad": 1,
    }]}).status_code == 404
    admin = api.post("/usuarios", json={
        "tipo": "administrador", "nombre": "Carlos", "email": "carlos@example.com",
    }).json()
    assert api.post("/pedidos", json={"cliente_id": admin["id"], "items": [{
        "producto_id": prod["id"], "cantidad": 1,
    }]}).status_code == 403
    assert api.get(f"/usuarios/{admin['id']}/pedidos").status_code == 403
    assert api.get("/usuarios/inexistente/pedidos").status_code == 404


def test_pedido_validaciones_y_duplicados(api):
    cliente = crear_cliente(api)
    prod = crear_producto(api)
    base = {"cliente_id": cliente["id"]}
    assert api.post("/pedidos", json={**base, "items": []}).status_code == 422
    assert api.post("/pedidos", json={**base, "items": [{
        "producto_id": prod["id"], "cantidad": 0,
    }]}).status_code == 422
    assert api.post("/pedidos", json={**base, "items": [
        {"producto_id": prod["id"], "cantidad": 1},
        {"producto_id": prod["id"], "cantidad": 2},
    ]}).status_code == 422
    assert api.get(f"/productos/{prod['id']}").json()["stock"] == 5


def test_alias_id_cliente_e_id_producto(api):
    cliente = crear_cliente(api)
    producto = crear_producto(api)
    respuesta = api.post("/pedidos", json={
        "id_cliente": cliente["id"],
        "items": [{"id_producto": producto["id"], "cantidad": 1}],
    })
    assert respuesta.status_code == 201


def test_interfaz_inicio_y_archivos_estaticos(api):
    inicio = api.get("/")
    assert inicio.status_code == 200
    assert "Tienda online" in inicio.text
    assert 'id="form-usuario"' in inicio.text
    assert 'id="form-producto"' in inicio.text
    assert 'id="form-pedido"' in inicio.text
    assert api.get("/static/estilos.css").status_code == 200
    assert api.get("/static/aplicacion.js").status_code == 200


def test_servidor_abre_navegador_tras_arrancar(monkeypatch):
    import asyncio
    import webbrowser

    import uvicorn

    from iniciar import ServidorLocal

    urls = []

    async def arranque_simulado(servidor, sockets=None):
        servidor.started = True

    monkeypatch.setattr(uvicorn.Server, "startup", arranque_simulado)
    monkeypatch.setattr(webbrowser, "open", urls.append)

    servidor = ServidorLocal(uvicorn.Config("main:app", log_level="warning"))
    asyncio.run(servidor.startup())
    assert urls == ["http://127.0.0.1:8000/"]
