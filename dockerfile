# Usamos una imagen oficial y ligera de Python
FROM python:3.10-slim

# Evita que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE=1
# Evita que Python almacene en el búfer stdout y stderr
ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instala dependencias del sistema necesarias para compilar paquetes
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean

# Instala las dependencias de Python
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia el proyecto
COPY . /app/