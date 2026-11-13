# Tienda online — miguel-rio-gavin-devops-practica

**Autor:** Miguel Río Gavin

Repositorio de las prácticas de DevOps (3.1 Git/GitHub y 3.2 Docker), construido sobre la aplicación Python de la Práctica 2.

## Descripción

Aplicación para gestionar una tienda online: usuarios (clientes y administradores), productos (genéricos, electrónicos y de ropa) y pedidos con control de stock. Incluye una **API REST** hecha con **FastAPI** y **Pydantic** y una **interfaz web** (HTML, CSS y JavaScript) que se sirve desde el mismo servidor.

La información se guarda **en memoria**, así que se borra al reiniciar el servidor o el contenedor.

## Estructura del repositorio

```text
miguel-rio-gavin-devops-practica/
├── Dockerfile              # Definición de la imagen Docker
├── .dockerignore           # Ficheros excluidos al construir la imagen
├── .gitignore
├── requirements.txt        # Dependencias con versiones fijadas
├── requirements-dev.txt    # Dependencias para las pruebas
├── pytest.ini
├── README.md
└── src/                    # Código de la Práctica 2
    ├── main.py             # Rutas de la API y página de inicio
    ├── iniciar.py          # Arranque del servidor (configurable por variables de entorno)
    ├── iniciar.bat / iniciar.sh
    ├── web/                # Interfaz web
    ├── models/             # Usuario, Producto, Pedido
    ├── Services/           # Lógica de la tienda
    ├── schemas/            # Esquemas Pydantic
    └── tests/              # Pruebas de la API
```

## Ejecución sin Docker

Requiere Python 3.10 o superior.

```bash
python -m pip install -r requirements.txt
cd src
python main.py
```

Se abre el navegador en `http://localhost:8000`. Para parar el servidor, pulsa **Ctrl+C**.

## Docker

### 1. Construir la imagen

Desde la raíz del repositorio:

```bash
docker build -t tienda-online:1.0.0 .
docker tag tienda-online:1.0.0 tienda-online:latest
```

### 2. Ejecutar el contenedor

```bash
# En primer plano (Ctrl+C para parar)
docker run --rm -p 8000:8000 --name tienda tienda-online:1.0.0

# En segundo plano
docker run -d -p 8000:8000 --name tienda tienda-online:1.0.0

# Cambiando el puerto interno con una variable de entorno
docker run -d -p 9000:9000 -e PORT=9000 --name tienda tienda-online:1.0.0
```

Comandos útiles:

```bash
docker ps                 # ver contenedores en marcha y su estado (healthy)
docker logs -f tienda     # ver los logs
docker stop tienda        # parar
docker rm tienda          # borrar (si no se usó --rm)
```

### 3. Variables de entorno soportadas

| Variable | Valor en la imagen | Descripción |
|---|---|---|
| `HOST` | `0.0.0.0` | Dirección en la que escucha el servidor. En local vale `127.0.0.1`. |
| `PORT` | `8000` | Puerto del servidor dentro del contenedor. |
| `ABRIR_NAVEGADOR` | `0` | `1` abre el navegador al arrancar (solo tiene sentido fuera de Docker). |
| `LOG_LEVEL` | `info` | Nivel de log de uvicorn (`debug`, `info`, `warning`, `error`). |

La aplicación no usa claves ni secretos.

### 4. Salida esperada y pruebas

Al arrancar, los logs deben mostrar algo parecido a:

```text
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Con el contenedor en marcha:

- Interfaz web: <http://localhost:8000>
- Documentación interactiva de la API (Swagger): <http://localhost:8000/docs>

Pruebas rápidas con `curl`:

```bash
# Listado de productos (al principio está vacío)
curl http://localhost:8000/productos
# -> []

# Crear un cliente
curl -X POST http://localhost:8000/usuarios \
  -H "Content-Type: application/json" \
  -d '{"tipo":"cliente","nombre":"Ana","email":"ana@example.com","direccion":"Calle Mayor, 1"}'
# -> 201 con {"id": "...", "nombre": "Ana", "email": "ana@example.com", "es_admin": false}

# Crear un producto electrónico
curl -X POST http://localhost:8000/productos \
  -H "Content-Type: application/json" \
  -d '{"tipo":"electronico","nombre":"Portátil","precio":800,"stock":5,"meses_garantia":24}'
# -> 201 con los datos del producto y su id

# Crear un pedido (sustituye los id por los devueltos antes)
curl -X POST http://localhost:8000/pedidos \
  -H "Content-Type: application/json" \
  -d '{"cliente_id":"<ID_CLIENTE>","items":[{"producto_id":"<ID_PRODUCTO>","cantidad":2}]}'
# -> 201 con el pedido, total 1600.0, y el stock del portátil baja a 3
```

En PowerShell (Windows) se puede usar `Invoke-RestMethod http://localhost:8000/productos`.

La imagen incluye un `HEALTHCHECK` que consulta `/productos`; `docker ps` muestra el contenedor como `healthy` cuando responde.

### 5. Publicar la imagen en un registry (push)

La imagen está publicada en **GitHub Container Registry**: `ghcr.io/miguelrio01/tienda-online` (etiquetas `1.0.0` y `latest`).

La publicación es automática con **GitHub Actions** (`.github/workflows/docker.yml`). En cada cambio el flujo hace **build → run → test → push**:

1. Ejecuta las pruebas unitarias con `pytest`.
2. Construye la imagen con `docker build`.
3. Arranca el contenedor con `docker run`.
4. Prueba los endpoints con `curl`: crea un cliente, un producto y un pedido y comprueba el total y el stock.
5. Si el cambio es en `main`, sube la imagen al registry con `docker push`.

Para publicarla a mano desde un equipo:

```bash
echo <TOKEN_GITHUB> | docker login ghcr.io -u miguelrio01 --password-stdin
docker tag tienda-online:1.0.0 ghcr.io/miguelrio01/tienda-online:1.0.0
docker tag tienda-online:1.0.0 ghcr.io/miguelrio01/tienda-online:latest
docker push ghcr.io/miguelrio01/tienda-online:1.0.0
docker push ghcr.io/miguelrio01/tienda-online:latest
```

### 6. Descargar y ejecutar la imagen publicada (pull)

```bash
docker pull ghcr.io/miguelrio01/tienda-online:1.0.0
docker run -d -p 8000:8000 --name tienda ghcr.io/miguelrio01/tienda-online:1.0.0
```

### Buenas prácticas aplicadas

- Imagen base `python:3.12-slim` para reducir el tamaño.
- `requirements.txt` copiado antes que el código para aprovechar la caché de capas.
- `pip install --no-cache-dir` y versiones fijadas.
- `.dockerignore` que excluye `.git`, cachés, pruebas, lanzadores locales y ficheros `.env`.
- El contenedor se ejecuta con un usuario sin privilegios (`appuser`).
- Configuración mediante variables de entorno y etiquetas de versión (`1.0.0` y `latest`).

## API REST

| Método | Ruta | Acción |
|---|---|---|
| POST | `/usuarios` | Registrar usuario |
| GET | `/usuarios` | Listar usuarios |
| GET | `/usuarios/{usuario_id}` | Consultar usuario |
| POST | `/productos` | Añadir producto |
| GET | `/productos` | Listar productos |
| GET | `/productos/{producto_id}` | Consultar producto |
| DELETE | `/productos/{producto_id}` | Eliminar producto |
| POST | `/pedidos` | Registrar pedido |
| GET | `/usuarios/{cliente_id}/pedidos` | Consultar historial |

## Pruebas automáticas

Desde la raíz del repositorio:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Flujo de trabajo con Git

- `main`: rama principal, con el código estable.
- `feature/docker`: rama de la Práctica 3.2 con el `Dockerfile`, el `.dockerignore` y esta documentación. Se integra en `main` mediante un Pull Request.
