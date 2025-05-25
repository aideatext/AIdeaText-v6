FROM python:3.10

WORKDIR /app

ENV TORCH_IGNORE_DISABLED_CUDA_WARNINGS=1
ENV STREAMLIT_SERVER_ENABLE_WEBKIT_DEPRECATION=0

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorios necesarios con permisos adecuados
RUN mkdir -p /home/appuser/.streamlit && \
    mkdir -p /home/appuser/.config/matplotlib && \
    chmod -R 777 /home/appuser

# Configurar variables de entorno
ENV MPLCONFIGDIR=/home/appuser/.config/matplotlib
ENV STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Copiar archivos de la aplicación
COPY requirements.txt ./
COPY src/ ./src/

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Establecer usuario no root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]