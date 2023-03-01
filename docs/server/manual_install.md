# Ручная установка

## Ручная установка и конфигурирование WEGA Server
Первое что делаем это обновляем систему до последнего состояния:
```
# эта команда повышает права в консоли для выполнения всех остальных дейтсвий
sudo su  

apt update
apt dist-upgrade
```

После обновления выполняем перезагруку командой `reboot`

---
## Подготовка компонентов
### Установка необходимых пакетов для работы WEGA server
```bash
apt install lamp-server^ php-curl gnuplot-nox curl
```
### Настройка базы данных
Задаем мастер пароль для `MYSQL`, который позволит создавать новые базы
```bash
mysql
```
```mysql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YOUR_PASSWORD_HERE';
FLUSH PRIVILEGES;
SET GLOBAL log_bin_trust_function_creators = 1;
quit;
```
Пароль должен быть сложным (содержать буквы в разном регистре, цифры и знаки)

Для корректной работы необходимо добавить в конец `mysqld.cnf` дополнительный параметр:

`echo "log-bin-trust-function-creators = 1" >> /etc/mysql/mysql.conf.d/mysqld.cnf`

---
## Настройка WEGA
`WEGA-GUI` - это непосредственно графическая среда с отображением параметров и графиков устройств.

По умолчанию она доступна по адресу: `http://WEGA_SERVER_IP/wega`

### Настройка WEGA GUI
#### Загрузка последней версии проекта WEGA
```bash
apt install git
cd /var
git clone https://github.com/WEGA-project/WEGA.git
chown www-data:www-data -R /var/WEGA
```

#### Настройка web сервера
```bash
ln -s /var/WEGA/apache/WEGA.conf /etc/apache2/conf-enabled/
ln -s /var/WEGA/apache/wega-api.conf /etc/apache2/conf-enabled/

/etc/init.d/apache2 restart
```
#### Настройка авторизации для доступа к WEB консоли
*  Удаляем доступ без авторизации (если был настроен):
```rm /etc/apache2/conf-enabled/WEGA.conf```
* Создаем пользователя и пароль:
```htpasswd -c /etc/apache2/.htpasswd username```
 где username это логин
* Подключаем конфигурацию требующую авторизацию для доступа к страничке
```ln -s /var/WEGA/apache/WEGA-auth.conf /etc/apache2/conf-enabled/```
* Перезапускаем web сервер
```/etc/init.d/apache2 restart```

#### Настройка доступа сервера `WEGA` к базе данных
```bash
cp /var/WEGA/example.db.php /var/WEGA/db.php
nano /var/WEGA/db.php
```
Вносим пароль заданный на этапе настройки базы данных

---
### Настройка WEGA-API
`WEGA-API` - отвечает за получение данных от контроллеров сбора показаний сенсоров. Контроллеры подключаются к ней и передают измеренные значения. 

Каждому контроллеру соответствует свой файл api в котором указана база для записи данных и параметры подключения к ней.

#### Настраиваем подключение к базе данных для WEGA-API
Отредактируем файл примера:

указываем параметры подключения к базе для записи данных.

Создадим файл доступа к wega-api из файла примера:
```bash
cp /var/WEGA/example/wega-api/wegabox.php.example /var/WEGA/wega-api/wegabox.php
nano /var/WEGA/wega-api/wegabox.php
```
Тут главная задача, отредактировать строку, поменяв ключ доступа на свой. Этот ключи будет использовать устройство при отправке данных на сервер. 
$auth="73ad7a1144dfc58eb2585cde8a0f7a948338";

⚠️ **ВАЖНО: Один ключ = один api. Много устройств могут использовать один api, но можно создавать много api для разных устройств. ** ⚠️
---
### Проверка API post <a name="api_check"></a>

Выполним в браузере:

`http://WEGA_SERVER_IP/wega-api/wegabox.php?auth=adab637320e5c47624cdd15169276981&db=esp32wega&RootTemp=25&AirTemp=25&AirHum=50`

где 
* `ip-address-server` это адрес сервера

* `auth=adab637320e5c47624cdd15169276981` код доступа к `api` (должен быть задан в файле `/var/WEGA/wega-api/wegabox.php`)

* `db=esp32wega` имя в базы данных для записи(для каждого модуля `ESP` должна быть своя база данных)

Это действие создаст базу даных с таблицей `sens` и внесет тестовый набор сеносоров как будто все они показывают значение единица.

Войдем в интерфейс `WEGA` `http://ip-address-server/wega` выбираем `анализ -> таблица значений`. 

Мы должны увидить запись с меткой времени и единицами в полях значений.

Параметры обработки сенсоров расположены в каталоге:
```bash
#имя вашего конфиг файла и именем базы данных для вашей гидропонной системы
cd /var/WEGA/wegagui/config
cp example/example.conf.php esp32wega.conf.php 
nano esp32wega.conf.php 
```

Если у вас больше чем один модуль `WEGA-ESP32`, то вам не обходимо создать новый конфиг файл и так для каждого модуля `WEGA-ESP32`

Ниже можно видеть как создать еще один конфиг файл для второго модуля `WEGA-ESP32`

```bash
#имя вашего конфиг файла и именем базы данных для вашей гидропонной системы
cd /var/WEGA/wegagui/config
cp example/example.conf.php mainNFT.conf.php 
nano mainNFT.conf.php 
```

---
## Подключение погодного модуля OWM-LOG <a name="weather"></a>
Он нужен для получения данных о текущей погоде и ее логирования с последующим включением в состав графиков wega.
* Регистрируемся на сервисе и создаем api ключ на этой странице: `https://home.openweathermap.org/api_keys`
* Найти ближайшую точку можно на карте: `https://openweathermap.org/weathermap`

### Установка <a name="weather_install"></a>
`apt install curl jq`

* Создадим скрипт загрузки погоды, незабыв указать свой город и ключ в поля `sity`, `apikey`
```bash
nano /usr/bin/owm-log
```

* Добавим

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

* Делаем скрипт исполняемым и добавляем папку для логов
```bash
chmod +x /usr/bin/owm-log
mkdir /var/log/sensors
```

* Проверяем
```bash
owm-log
cat /var/log/sensors/owm.log
```

Если все прошло успешно в файл запишется текущее состояние погоды

* Назначим выполнение загрузки погоды по расписанию

* Откроем файл 
```bash
nano /etc/crontab
```

* И добавим туда в конец строку
```bash
*/15 * * * * root owm-log
```

Раз в 15 минут файл с погодой будет пополняться.
