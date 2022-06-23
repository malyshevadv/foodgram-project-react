# Дипломный проект "Продктовый помощник" (praktikum_new_diplom)

# Описание
На этом сервисе пользователи могут публиковать рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать сводный список продуктов, необходимых для приготовления одного или нескольких выбранных блюд.

### Доступ к странице на удаленном севрере

Адрес: http://praktikum-dm.hopto.org/

Адрес API: http://praktikum-dm.hopto.org/api

Адрес страницы администратора: http://praktikum-dm.hopto.org/api/admin

Для входа от имени администратора:
```
Логин: mainadmin@foodgram.gav
Пароль $up3rpass
```

![example workflow](https://github.com/malyshevadv/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

### Как запустить проект:
Проект работает на основе контейнеров. Для создания контейнеров из папки infra выполнить:
```
docker-compose up -d --build
```

Для запуска на основе готовых контейнеров:
```
docker-compose pull
docker-compose up -d --no-build
```

При первом деплое выполнить:
```
docker-compose exec web-food python manage.py makemigrations
docker-compose exec web-food python manage.py migrate --no-input
docker-compose exec web-food python manage.py collectstatic --no-input
docker-compose exec web-food python manage.py load_ingredients
docker-compose exec web-food python manage.py load_tags
```


### CI/CD
В проекте реализовано автоматическое развертывание проекта на базе GitHub.Actions:
- автоматический запуск тестов,
- обновление образов на Docker Hub,
- автоматический деплой на боевой сервер при пуше в главную ветку main.

### Примеры запросов:

Примеры запросов и документация доступны по ссылке http://praktikum-dm.hopto.org/api/docs/redoc.html

### Технологии
- Python 3.7
- Django 2.2.19

### Авторы
Дарья Малышева
