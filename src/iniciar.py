"""Inicia la tienda y, si se ejecuta en el equipo, abre su interfaz en el navegador.

La configuración se lee de variables de entorno para poder ejecutarla tanto
en local como dentro de un contenedor Docker:

- HOST: dirección en la que escucha el servidor (por defecto 127.0.0.1).
- PORT: puerto del servidor (por defecto 8000).
- ABRIR_NAVEGADOR: "1" para abrir el navegador al arrancar, "0" para no hacerlo
  (por defecto 1). En Docker se pone a 0.
- LOG_LEVEL: nivel de log de uvicorn (por defecto info).
"""

import os
import webbrowser

import uvicorn

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
ABRIR_NAVEGADOR = os.getenv("ABRIR_NAVEGADOR", "1") == "1"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")


class ServidorLocal(uvicorn.Server):
    async def startup(self, sockets=None):
        await super().startup(sockets=sockets)
        if self.started and ABRIR_NAVEGADOR:
            webbrowser.open(f"http://127.0.0.1:{PORT}/")


def iniciar_servidor():
    configuracion = uvicorn.Config(
        "main:app", host=HOST, port=PORT, log_level=LOG_LEVEL
    )
    ServidorLocal(configuracion).run()


if __name__ == "__main__":
    iniciar_servidor()
