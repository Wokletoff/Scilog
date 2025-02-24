FROM python:3.9-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения в контейнер
COPY website_LLM_meta_text_search.py .

# Открываем порт 5000 для Flask-приложения
EXPOSE 5000

# Монтируем внешнюю папку с данными
VOLUME /mnt/disk2

# Команда для запуска приложения
CMD ["python", "website_LLM_meta_text_search.py"]