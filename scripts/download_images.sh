#!/bin/bash
set -euo pipefail

# Создаем директорию, если она не существует
mkdir -p docs/assets

# Читаем файл с URL-ами и скачиваем каждый
while IFS= read -r url; do
  # Убираем возможные CR и пропускаем пустые/мусорные строки и комментарии
  url="${url%$'\r'}"
  if [[ -z "$url" || "$url" == "." || "$url" =~ ^# ]]; then
    continue
  fi

  # Извлекаем имя файла из URL и декодируем его
  filename=$(basename "$url")
  decoded_filename=$(python3 -c "import urllib.parse,sys; print(urllib.parse.unquote(sys.argv[1]))" "$filename")

  # Пропускаем, если файл уже скачан
  if [[ -f "docs/assets/$decoded_filename" ]]; then
    echo "Skip $decoded_filename (exists)"
    continue
  fi

  # Скачиваем файл
  echo "Downloading $decoded_filename..."
  curl -fL --retry 3 --connect-timeout 10 --max-time 120 "$url" -o "docs/assets/$decoded_filename"
done < image_urls.txt

echo "Download complete."
