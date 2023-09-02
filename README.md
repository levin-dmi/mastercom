## Установка/обновление проекта на хостинге timeweb
- Сделать всех пользователей кроме администратора неактивными
- Убедиться что есть резервная копия
- Заменить файлы на хостинге новыми
- Удалить mastercom/local_settings.py
- Запустить ssh консоль и venv: 'source /home/m/mastercom/my/public_html/venv/bin/activate'
- Перейти в каталог 'cd /home/m/mastercom/my/public_html/mastercom'
- Установить недостающие пакеты 'pip install'
- Запустить 'python manage.py collectstatic'
- (тут не понятно, вроде должен файлы из assets или cкопировать в static или видеть а сам не то не другое. копировал вручную.)
- Запустить миграции 'python manage.py migrate'
- Проверить результат и включить пользователей

## Настройка рассылок
Создать в корне сайта файл sendnews.sh
`#!/bin/sh 
/home/m/mastercom/my/public_html/venv/bin/python /home/m/mastercom/my/public_html/mastercom/manage.py send_news levin@mastercom.su kd@mastercom.su`
Дать ему права на запуск и добавить в крон
