# Краткое описание

Социальная сеть для блогов на базе Django, с помощью котрой можно:
- Зарегестрироваться на сайте или войти в уже существующий аккаунт
- Просматривать, создавать и изменять посты
- Просматривать  сообщества
- Писать комментарии
- Подписываться на авторов и просматривать свои подписки

Неавторизированные пользователи могут только просматривать посты, комментарии, сообщества

# Порядок запуска приложения 

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Ander-dog/yatube.git
```

```
cd yatube
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

* Если у вас Linux/macOS

    ```
    source venv/bin/activate
    ```

* Если у вас windows

    ```
    source venv/scripts/activate
    ```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Применить миграции:

```
cd yatube/
```

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

# Список использованных технологий

- Python3.7 (язык разработки бэкенда)
- Django (фрэймворк приложения)
- HTML (язык разработки фронтэнда)
- Django ORM (для работы с базами данных)
- pytest (для тестирования работы приложения)

# Автор

[Андрей А.](https://github.com/Ander-dog)
