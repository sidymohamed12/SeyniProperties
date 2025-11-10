# Dockerfile - Configuration personnalisée pour Railway
FROM python:3.12-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Création du répertoire de travail
WORKDIR /app

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Création du répertoire pour les fichiers statiques
RUN mkdir -p /app/staticfiles

# Rendre le script de démarrage exécutable
RUN chmod +x start.sh

# Exposition du port
EXPOSE 8000

# Commande de démarrage (migrations au runtime)
CMD ["./start.sh"]