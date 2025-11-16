
## Ручная установка и конфигурирование WEGA Server
Первое что делаем это обновляем систему до последнего состояния:
 <code># эта команда повышает права в консоли для выполнения всех остальных дейтсвий
 sudo su  
 
 apt update
 apt dist-upgrade</code>
После обновления выполняем перезагруку командой <code>reboot</code>
----

## Подготовка компонентов
### Установка необходимых пакетов для работы WEGA server
 apt install lamp-server^ php-curl gnuplot-nox curl

#### Настройка базы данных
Задаем мастер пароль для <code>MYSQL</code>, который позволит создавать новые базы
 mysql

 ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YOUR_PASSWORD_HERE';
 FLUSH PRIVILEGES;
 SET GLOBAL log_bin_trust_function_creators = 1;
 quit;
Пароль должен быть сложным (содержать буквы в разном регистре, цифры и знаки)

Для корректной работы необходимо добавить в конец <code>mysqld.cnf</code> дополнительный параметр:

<code>echo "log-bin-trust-function-creators = 1" >> /etc/mysql/mysql.conf.d/mysqld.cnf</code>
----

## Настройка WEGA
<code>WEGA-GUI</code> - это непосредственно графическая среда с отображением параметров и графиков устройств.

По умолчанию она доступна по адресу: <code><nowiki>http://WEGA_SERVER_IP/wega</nowiki></code>

### Настройка WEGA GUI
#### Загрузка последней версии проекта WEGA
 apt install git
 cd /var
 git clone <nowiki>https://github.com/WEGA-project/WEGA.git</nowiki>
 chown www-data:www-data -R /var/WEGA

#### Настройка web сервера
 ln -s /var/WEGA/apache/WEGA.conf /etc/apache2/conf-enabled/
 ln -s /var/WEGA/apache/wega-api.conf /etc/apache2/conf-enabled/
 
 /etc/init.d/apache2 restart

#### Настройка авторизации для доступа к WEB консоли
* Удаляем доступ без авторизации (если был настроен): <code>rm /etc/apache2/conf-enabled/WEGA.conf</code>
* Создаем пользователя и пароль: <code>htpasswd -c /etc/apache2/.htpasswd username</code> где username это логин
* Подключаем конфигурацию требующую авторизацию для доступа к страничке <code>ln -s /var/WEGA/apache/WEGA-auth.conf /etc/apache2/conf-enabled/</code>
* Перезапускаем web сервер <code>/etc/init.d/apache2 restart</code>

#### Настройка доступа сервера <code>WEGA</code> к базе данных
 cp /var/WEGA/example.db.php /var/WEGA/db.php
 nano /var/WEGA/db.php
Вносим пароль заданный на этапе настройки базы данных
----

### Настройка WEGA-API
<code>WEGA-API</code> - отвечает за получение данных от контроллеров сбора показаний сенсоров. Контроллеры подключаются к ней и передают измеренные значения.

Каждому контроллеру соответствует свой файл api в котором указана база для записи данных и параметры подключения к ней.

#### Настраиваем подключение к базе данных для WEGA-API
Отредактируем файл примера:

указываем параметры подключения к базе для записи данных.

Создадим файл доступа к wega-api из файла примера:
 cp /var/WEGA/example/wega-api/wegabox.php.example /var/WEGA/wega-api/wegabox.php
 nano /var/WEGA/wega-api/wegabox.php
Тут главная задача, отредактировать строку, поменяв ключ доступа на свой. Этот ключи будет использовать устройство при отправке данных на сервер. $auth="73ad7a1144dfc58eb2585cde8a0f7a948338";

## **ВАЖНО: Один ключ = один api. Много устройств могут использовать один api, но можно создавать много api для разных устройств. **
### Проверка API post
Выполним в браузере:

<code><nowiki>http://WEGA_SERVER_IP/wega-api/wegabox.php?auth=adab637320e5c47624cdd15169276981&db=esp32wega&RootTemp=25&AirTemp=25&AirHum=50</nowiki></code>

где

* <code>ip-address-server</code> это адрес сервера
* <code>auth=adab637320e5c47624cdd15169276981</code> код доступа к <code>api</code> (должен быть задан в файле <code>/var/WEGA/wega-api/wegabox.php</code>)
* <code>db=esp32wega</code> имя в базы данных для записи(для каждого модуля <code>ESP</code> должна быть своя база данных)

Это действие создаст базу даных с таблицей <code>sens</code> и внесет тестовый набор сеносоров как будто все они показывают значение единица.

Войдем в интерфейс <code>WEGA</code> <code><nowiki>http://ip-address-server/wega</nowiki></code> выбираем <code>анализ -> таблица значений</code>.

Мы должны увидить запись с меткой времени и единицами в полях значений.

Параметры обработки сенсоров расположены в каталоге:
 #имя вашего конфиг файла и именем базы данных для вашей гидропонной системы
 cd /var/WEGA/wegagui/config
 cp example/example.conf.php esp32wega.conf.php 
 nano esp32wega.conf.php 
Если у вас больше чем один модуль <code>WEGA-ESP32</code>, то вам не обходимо создать новый конфиг файл и так для каждого модуля <code>WEGA-ESP32</code>

Ниже можно видеть как создать еще один конфиг файл для второго модуля <code>WEGA-ESP32</code>
 #имя вашего конфиг файла и именем базы данных для вашей гидропонной системы
 cd /var/WEGA/wegagui/config
 cp example/example.conf.php mainNFT.conf.php 
 nano mainNFT.conf.php