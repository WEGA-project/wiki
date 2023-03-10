# Установка через скрипт
В данном разделе вы узнаете как установить WEGA Server и выполнить минимальное конфигурирование через скрипт.
На данный момент официально поддерживается две системы это `Ubuntu 20.04` и `Ubuntu 22.04`.

Скрипт проверн на `OS`, которые были установлены на `VirtualBox` и `AWS`.

Т.е. скрипт можно использовать как локально, так и в cloud(клауде).

=== "Ubuntu 20.04"

    * Установить `ubuntu server 20.04` на виртуальную машину или любой клауд (AWS, GCP, Azure, Oracle)

    * Подключиться по `ssh` к серверу

    * Скопировать и выполнить на сервере следущее
    ``` 
    sudo su
    wget -O - https://raw.githubusercontent.com/WEGA-project/wega/master/install.sh | bash
    ```

=== "Ubuntu 22.04"

    * Установить `ubuntu server 22.04` на виртуальную машину или любой клауд (AWS, GCP, Azure, Oracle)

    * Подключиться по `ssh` к серверу

    * Скопировать и выполнить на сервере следущее
    ``` 
    sudo su
    wget -O - https://raw.githubusercontent.com/WEGA-project/wega/master/install-ubuntu-2204.sh | bash
    ```

    * Пойти выпить чаю или еще чего, пока идет настройка и конфигурирование
    * Прочитать информацию после установки, где будет написано, как зайти через веб интерфейс на ваш свеже-установленный `WEGA SERVER`
    * Не забыть скопировать и сохранить информацию для веб доступа и `WEGABOX`

=== "Видео установки WEGA SERVER"
    <iframe width="560" height="315" src="https://www.youtube.com/embed/TOMY-anSX0E" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>


⚠️ **ВАЖНО: Если решили поднимать сервер на AWS, помните про security groups(доступ к серверу необходимо разрешить для вашего IP адреса на 80 порт)** ⚠️