# praktikum_new_diplom


# api_final
Финальная версия проекта API для Yatube: данное API позволяет просматривать списки существующих постов авторов, создавать, редактировать, изменять, удалять существующие посты, просматривать, оставлять редактировать, создавать комментарии к существующим постам, просматривать список групп, а также подписываться на авторов и просматривать списки подписок. 

### Доступ к странице на удаленном севрере

Адрес: http://praktikum-dm.hopto.org/
Адрес API: http://praktikum-dm.hopto.org/api
Адрес страницы администратора: http://praktikum-dm.hopto.org/api/admin

Для входа от имени администратора:
```
Логин: mainadmin@foodgram.gav
Пароль $up3rpass]
```

![example workflow](https://github.com/malyshevadv/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

### Как запустить проект:
Проект работает на основе контейнеров. Для создания контейнеров из папки infra выполнить:
```
docker-compose up -d --build
```

При первом деплое выполнить:
```
docker-compose exec web-food python manage.py makemigrations
docker-compose exec web-food python manage.py migrate --no-input
docker-compose exec web-food python manage.py collectstatic --no-input
docker-compose exec web-food python manage.py load_ingredients
```
### Примеры запросов:

Примеры запросов и документация доступны по ссылке http://praktikum-dm.hopto.org/api/docs/redoc.html
