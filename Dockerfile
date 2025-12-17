# 1. Imagem Base
FROM python:3.11-slim

# 2. Variáveis de Ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Instalação do Google Chrome (Método Moderno e Corrigido)
RUN apt-get update && \
    apt-get install -y curl gnupg --no-install-recommends && \
    curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google.gpg && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 4. Diretório de Trabalho
WORKDIR /app

# 5. Instalação de Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Cópia do Código da Aplicação
COPY . .

# 7. Exposição da Porta
EXPOSE 5000

# 8. Comando de Execução
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]

