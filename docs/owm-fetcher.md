# OWM Fetcher

![Пример отображения погоды в WEGA-GUI](assets/owm1.png)

## Подключение погодного модуля

Модуль нужен для получения данных о текущей погоде, их логирования и включения в графики `WEGA`.

- Регистрируемся в сервисе и создаём API-ключ: `https://home.openweathermap.org/api_keys`.
- Ищем ближайшую точку на карте: `https://openweathermap.org/weathermap`.

### Установка

```bash
apt install curl jq
```

Создаём скрипт загрузки погоды, указав свой город и ключи в параметрах `sity`, `apikey`, `wegaapikey`:

```bash
nano /usr/bin/owm-log
```

Добавляем содержимое:

```bash
#!/bin/bash
sity="Khabarovsk,ru"
apikey="XXXXXXXXXXXXX"
wegaapikey="ХХХХХХХХХХХХ"

curl "http://api.openweathermap.org/data/2.5/weather?q=$sity&appid=$apikey" > /run/shm/owm
sdate=`date '+%Y-%m-%d %H:%M:%S'`
hum=`jq -r ".main.humidity" /run/shm/owm`
pressure=`jq -r ".main.pressure" /run/shm/owm`
temp=`jq -r ".main.temp" /run/shm/owm|awk -F ":" '{print $1-273.15}'`
clouds=`jq -r ".clouds.all" /run/shm/owm`

echo "$sdate;$temp;$hum;$pressure;$clouds" >> /var/log/sensors/owm.log
curl `echo "http://127.0.0.1/wega-api/wegabox.php?db=owm&auth=$wegaapikey&temp=$temp&hum=$hum&pressure=$pressure&clouds=$clouds" | sed -e s/,/./g`
```

Делаем скрипт исполняемым и создаём директорию для логов:

```bash
chmod +x /usr/bin/owm-log
mkdir /var/log/sensors
```

Проверяем работу:

```bash
owm-log
cat /var/log/sensors/owm.log
```

При успешном выполнении в файл добавится запись о текущей погоде.

Назначаем выполнение скрипта по расписанию. Открываем crontab:

```bash
nano /etc/crontab
```

Добавляем строку:

```cron
*/15 * * * * root owm-log
```

Скрипт будет запускаться каждые 15 минут и обновлять данные о погоде.
