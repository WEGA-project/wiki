# Ручная установка и конфигурирование WEGA Server

## Обновление системы

```bash
# эта команда повышает права в консоли для выполнения всех остальных действий
sudo su

apt update
apt dist-upgrade
reboot
```

---

## Подготовка компонентов

### Установка необходимых пакетов для работы WEGA Server

```bash
apt install lamp-server^ php-curl gnuplot-nox curl
```

### Настройка базы данных

Задаём мастер-пароль для `MySQL`, чтобы можно было создавать новые базы данных:

```sql
mysql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YOUR_PASSWORD_HERE';
FLUSH PRIVILEGES;
SET GLOBAL log_bin_trust_function_creators = 1;
quit;
```

Пароль должен быть сложным (содержать буквы в разном регистре, цифры и специальные символы).

Для корректной работы добавляем в конец `mysqld.cnf` дополнительный параметр:

```bash
echo "log-bin-trust-function-creators = 1" >> /etc/mysql/mysql.conf.d/mysqld.cnf
```

---

## Настройка WEGA

`WEGA-GUI` — графическая среда с отображением параметров и графиков устройств. По умолчанию доступна по адресу `http://WEGA_SERVER_IP/wega`.

### Настройка WEGA GUI

#### Загрузка последней версии проекта WEGA

```bash
apt install git
cd /var
git clone https://github.com/WEGA-project/WEGA.git
chown www-data:www-data -R /var/WEGA
```

#### Настройка веб-сервера

```bash
ln -s /var/WEGA/apache/WEGA.conf /etc/apache2/conf-enabled/
ln -s /var/WEGA/apache/wega-api.conf /etc/apache2/conf-enabled/
/etc/init.d/apache2 restart
```

#### Настройка авторизации для доступа к веб-консоли

- Удаляем доступ без авторизации (если был настроен):

  ```bash
  rm /etc/apache2/conf-enabled/WEGA.conf
  ```

- Создаём пользователя и пароль:

  ```bash
  htpasswd -c /etc/apache2/.htpasswd username
  ```

  где `username` — логин.

- Подключаем конфигурацию, требующую авторизацию:

  ```bash
  ln -s /var/WEGA/apache/WEGA-auth.conf /etc/apache2/conf-enabled/
  ```

- Перезапускаем веб-сервер:

  ```bash
  /etc/init.d/apache2 restart
  ```

#### Настройка доступа сервера WEGA к базе данных

```bash
cp /var/WEGA/example.db.php /var/WEGA/db.php
nano /var/WEGA/db.php
```

В файле `db.php` указываем пароль, заданный на этапе настройки базы данных.

---

### Настройка WEGA-API

`WEGA-API` отвечает за получение данных от контроллеров. Каждому контроллеру соответствует свой файл API с параметрами базы данных и ключом доступа.

#### Настраиваем подключение к базе данных для WEGA-API

Редактируем файл примера, указывая параметры подключения:

```bash
cp /var/WEGA/example/wega-api/wegabox.php.example /var/WEGA/wega-api/wegabox.php
nano /var/WEGA/wega-api/wegabox.php
```

Главная задача — отредактировать строку с ключом доступа (`$auth`). Этот ключ будет использовать устройство при отправке данных на сервер.

> **Важно:** один ключ = один API. Несколько устройств могут использовать один API, но можно создавать отдельные API для разных устройств.

#### Проверка API POST

Выполняем в браузере:

```
http://WEGA_SERVER_IP/wega-api/wegabox.php?auth=adab637320e5c47624cdd15169276981&db=esp32wega&RootTemp=25&AirTemp=25&AirHum=50
```

Параметры запроса:

- `WEGA_SERVER_IP` — адрес сервера.
- `auth` — код доступа к API (задан в `/var/WEGA/wega-api/wegabox.php`).
- `db` — имя базы данных для записи (для каждого модуля `ESP` используется своя база).

Запрос создаст базу `sens` и добавит тестовые значения. Затем проверяем интерфейс WEGA: `http://WEGA_SERVER_IP/wega` → **Анализ → Таблица значений** — должны увидеть запись с единицами.

Параметры обработки сенсоров находятся в каталоге:

```bash
cd /var/WEGA/wegagui/config
cp example/example.conf.php esp32wega.conf.php
nano esp32wega.conf.php
```

Если у вас несколько модулей `WEGA-ESP32`, создаём отдельные конфигурационные файлы. Пример для второго модуля:

```bash
cd /var/WEGA/wegagui/config
cp example/example.conf.php mainNFT.conf.php
nano mainNFT.conf.php
```
