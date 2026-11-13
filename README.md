# miguel-rio-gavin-devops-practica

Miguel Río Gavin

Tienda online de la Práctica 2 hecha con FastAPI. Permite gestionar usuarios, productos y pedidos desde una web o desde la API. Los datos se guardan en memoria, así que se pierden al reiniciar.

El código está en la carpeta `src`.

## Docker

Construir la imagen:

```
docker build -t tienda-online:1.0.0 .
```

Ejecutarla:

```
docker run -d -p 8000:8000 --name tienda tienda-online:1.0.0
```

Después se puede abrir en el navegador `http://localhost:8000` (la web) o `http://localhost:8000/docs` (la API).

Para pararla:

```
docker stop tienda
docker rm tienda
```

### Variables de entorno

- `PORT`: puerto del servidor (8000 por defecto)
- `HOST`: dirección donde escucha (0.0.0.0 en Docker)
- `LOG_LEVEL`: nivel de log (info por defecto)

Ejemplo cambiando el puerto:

```
docker run -d -p 9000:9000 -e PORT=9000 --name tienda tienda-online:1.0.0
```

### Pruebas

Al arrancar, `docker logs tienda` tiene que mostrar `Uvicorn running on http://0.0.0.0:8000`.

Algunas pruebas con curl:

```
curl http://localhost:8000/productos

curl -X POST http://localhost:8000/usuarios -H "Content-Type: application/json" -d '{"tipo":"cliente","nombre":"Ana","email":"ana@example.com","direccion":"Calle Mayor 1"}'

curl -X POST http://localhost:8000/productos -H "Content-Type: application/json" -d '{"tipo":"electronico","nombre":"Portatil","precio":800,"stock":5,"meses_garantia":24}'
```

La primera devuelve `[]` si no hay productos y las otras dos devuelven el usuario y el producto creados.

También hay tests con pytest:

```
pip install -r requirements-dev.txt
pytest
```

### Imagen publicada

La imagen está subida a GitHub Container Registry. Se sube sola con GitHub Actions (`.github/workflows/docker.yml`) cada vez que hay cambios en `main`, después de construirla y probarla.

Descargarla y ejecutarla:

```
docker pull ghcr.io/miguelrio01/tienda-online:1.0.0
docker run -d -p 8000:8000 --name tienda ghcr.io/miguelrio01/tienda-online:1.0.0
```
