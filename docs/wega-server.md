![пример интерфейса WEGA-SERVER](assets/screen2.png)

## Что такое WEGA-Server

Это WEB сервер в стандарте [LAMP](https://ru.wikipedia.org/wiki/LAMP). Роль сервера - объединять все компоненты проекта в единое целое. Отображать графики значений и подсказки по выращиванию, а так же выполнять калибровку датчиков. В wega-server входят следующие компоненты:
*   **[WEGA-GUI](wega-gui.md)** - модуль отображения статистики измерений выдает данные по фактическому состоянию растворов
*   **[WEGA-DB](wega-db.md)** - хранит данные со всех сенсоров и миксера
*   **[WEGA-API](wega-api.md)** - осуществляет прием данных и передачу параметров на устройства
*   **[WEGA-EVENT](wega-event.md)** - производит уведомление о ситуациях через **telegram bot**
*   **[SYSLOG](syslog.md)** - сервер сбора логов работы устройств
*   **[OWM Fetcher](owm-fetcher.md)** - компонент получающий погоду с сервиса [Open Weather Map](https://openweathermap.org/)
*   **[GRAFANA](grafana.md)** - мощный и удобный компонент визуализации измерений (значения графики отчеты)

## Поддержка проекта

Страница проекта на [github.com](https://github.com/WEGA-project/wega)

Telegram канал: [https://t.me/WEGA_SERVER/20740](https://t.me/WEGA_SERVER/20740) и старый [https://t.me/WEGA_SERVER/4](https://t.me/WEGA_SERVER/4)

## Развертывание

WEGA-SERVER может быть развернут на множестве операционных систем и устройств, везде где поддерживается набор технологий LAMP но официально проектом поддерживается:
*   X86_64 совместимый компьютер или виртуальная машина
*   Микрокомпьютер Orange Pi Zero 2 ([подробнее](https://t.me/WEGA_SERVER/1/12532))
*   любой облачный VDS сервис (AWS, GCP, Azure, Oracle) и подобный

Официально поддерживаемая операционная система **Ubuntu 20.04 LTS** ([установка](install-ubuntu.md))

При соблюдении требований сервер со всеми компонентами может быть развернут автоматизированно с помощью установочного скрипта:

```bash
sudo su
wget -O - https://raw.githubusercontent.com/WEGA-project/wega/master/install.sh | bash
```

> ''Внимание, замечены блокировки со стороны серверов grafana, что может приводить к проблемам автоустановки. Для обхода рекомендуется запускать скрипт через'' **torsocs**

![пример интерфейса wega в grafana](assets/screen1.png)

<iframe width="560" height="315" src="https://www.youtube.com/embed/TOMY-anSX0E" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

## Ручная установка

[Ручная установка WEGA-SERVER](manual-install.md)
