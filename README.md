## Установка/обновление проекта на хостинге timeweb
- Сделать всех пользователей кроме администратора неактивными
- Убедиться что есть резервная копия
- Заменить файлы на хостинге новыми
- Удалить mastercom/local_settings.py
- Скопировать файлы из incoming/static в каталог static в корне сайта
- Запустить ssh консоль и venv: 'source /home/m/mastercom/my/public_html/venv/bin/activate'
- Установить недостающие пакеты 'pip install'
- Запустить миграции 'cd /home/m/mastercom/my/public_html/mastercom'
- 'python manage.py migrate'
- Проверить результат и включить пользователей

## Настройка рассылок
Создать в корне сайта файл sendnews.sh
`#!/bin/sh 
/home/m/mastercom/my/public_html/venv/bin/python /home/m/mastercom/my/public_html/mastercom/manage.py send_news levin@mastercom.su kd@mastercom.su`
Дать ему права на запуск и добавить в крон
