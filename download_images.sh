#!/bin/bash

# Создаем директорию, если она не существует
mkdir -p docs/assets

# Читаем файл с URL-ами и скачиваем каждый
while IFS= read -r url; do
  # Извлекаем имя файла из URL и декодируем его
  filename=$(basename "$url")
  decoded_filename=$(python3 -c "import urllib.parse; print(urllib.parse.unquote('$filename'))")
  
  # Скачиваем файл
  echo "Downloading $decoded_filename..."
  curl -L "$url" -o "docs/assets/$decoded_filename"
done < image_urls.txt

echo "Download complete."
