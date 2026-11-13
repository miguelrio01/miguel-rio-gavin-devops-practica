# Imagen de la Tienda online (Práctica 2) - Práctica 3.2 DevOps
# a. Imagen base ligera de Python 3.12
FROM python:3.12-slim

# Evita ficheros .pyc y hace que los logs salgan al momento
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    ABRIR_NAVEGADOR=0 \
    LOG_LEVEL=info

WORKDIR /app

# b. Se copian primero las dependencias para aprovechar la caché de capas
COPY requirements.txt .

# c. Instalación de las librerías con versiones fijadas
RUN pip install --no-cache-dir -r requirements.txt

# d. Copia del código fuente
COPY src/ .

# e. Usuario sin privilegios y permisos para que pueda ejecutar el código
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app \
    && chmod -R u+rX /app
USER appuser

EXPOSE 8000

# Comprueba que la API responde
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request as u; u.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/productos')" || exit 1

# f. Comando de inicio
CMD ["python", "iniciar.py"]
