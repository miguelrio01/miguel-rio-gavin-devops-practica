"""Inicia la tienda y abre la web en el navegador."""

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
