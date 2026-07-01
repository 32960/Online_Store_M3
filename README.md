
# 🍺 Hop & Barley — Интернет-магазин для пивоварения

Полнофункциональный интернет-магазин для домашних пивоваров, разработанный на Django с REST API, JWT-аутентификацией и автоматической документацией Swagger.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Django](https://img.shields.io/badge/Django-6.0.5-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📋 Содержание

- [Возможности](#-возможности)
- [Технологический стек](#️-технологический-стек)
- [Структура проекта](#-структура-проекта)
- [Установка и запуск](#-установка-и-запуск)
- [Переменные окружения](#-переменные-окружения)
- [API документация](#-api-документация)
- [Корзина и сессии](#-api-документация)
- [Примеры запросов](#-примеры-запросов)
- [Тестирование и линтеры](#-тестирование-и-линтеры)
- [Чек-лист реализации](#-чек-лист-реализации)

## ✨ Возможности

### 🛒 Каталог товаров
- Список товаров с пагинацией (6 товаров на страницу)
- Фильтрация по категориям (множественный выбор)
- Фильтрация по диапазону цен (от/до)
- Поиск по названию и описанию
- Сортировка по цене, рейтингу, дате добавления
- Детальная страница товара с техническими характеристиками
- Динамические характеристики товаров (JSONField)

### 🛍️ Корзина и заказы
- Добавление товаров в корзину (сессии)
- Изменение количества и удаление товаров
- Предупреждения об изменении цены
- Оформление заказа с автозаполнением из последнего адреса
- Email-уведомления пользователю и администратору
- Автоматическое сохранение адреса после заказа
- Страница успешного заказа с деталями

### 👤 Личный кабинет
- Регистрация с автоматическим входом
- Вход по email (кастомная аутентификация)
- Редактирование профиля с валидацией email
- Смена пароля без разлогинивания
- История заказов с пагинацией
- **Фильтрация заказов** по статусу и диапазону дат
- Детальный просмотр заказа с товарами
- Отмена заказа с автоматическим возвратом stock
- Управление адресами (CRUD) с защитой от дубликатов

### ⭐ Отзывы и рейтинги
- Создание отзывов только после покупки
- Защита от дубликатов (UniqueConstraint)
- Рейтинг 1-5 звёзд
- Отображение последних 3 отзывов на странице товара
- Автоматический пересчёт рейтинга товара через signals

### 🔌 REST API
- Полноценный REST API для всех сущностей
- JWT-аутентификация (access/refresh токены)
- Endpoints для товаров, категорий, заказов, корзины, отзывов
- Swagger UI и ReDoc для интерактивной документации
- Примеры запросов с JWT

### 🛠️ Админ-панель
- Dashboard с аналитикой продаж
- Статистика заказов по статусам
- Топ-5 товаров по выручке
- Bulk actions для активации/деактивации товаров
- Управление пользователями, заказами, отзывами

## 🛠️ Технологический стек

### Backend
- **Python 3.14** — язык программирования
- **Django 6.0.5** — веб-фреймворк
- **Django REST Framework 3.16** — REST API
- **PostgreSQL 17** — база данных
- **django-filter 25.1** — фильтрация
- **Pillow 11.2** — обработка изображений
- **psycopg[binary] 3.2.9** — драйвер PostgreSQL

### Аутентификация и API
- **djangorestframework-simplejwt 5.5** — JWT токены
- **drf-spectacular 0.28** — OpenAPI/Swagger документация

### Инструменты разработки
- **mypy 1.17** — статическая типизация
- **django-stubs 5.2** — type hints для Django
- **pytest 9.0** — тестирование
- **pytest-django 4.12** — интеграция pytest с Django
- **python-dotenv 1.1** — переменные окружения

## 📁 Структура проекта


```

Online_Store_M3/
├── config/                  # Настройки проекта
│   ├── settings.py         # Основные настройки
│   ├── urls.py             # Корневой URLconf
│   └── wsgi.py             # WSGI конфигурация
│
├── api/                     # REST API приложение
│   ├── views.py            # API viewsets
│   ├── serializers.py      # DRF serializers
│   └── urls.py             # API endpoints
│
├── products/                # Каталог товаров
│   ├── models.py           # Product, Category
│   ├── views.py            # ProductListView, ProductDetailView
│   ├── admin.py            # Админ-панель
│   ├── services.py         # Пересчёт рейтинга
│   └── signals.py          # Автоматическое обновление рейтинга
│
├── orders/                  # Заказы и корзина
│   ├── models.py           # Order, OrderItem
│   ├── views.py            # CheckoutView, cart views
│   ├── cart.py             # Логика корзины (сессии)
│   └── forms.py            # CheckoutForm
│
├── users/                   # Пользователи и адреса
│   ├── models.py           # User (кастомный), Address
│   ├── views.py            # Регистрация, вход, кабинет
│   ├── forms.py            # Формы аутентификации
│   └── admin.py            # Админ-панель пользователей
│
├── reviews/                 # Отзывы и рейтинги
│   ├── models.py           # Review
│   ├── views.py            # ReviewCreateView
│   ├── services.py         # Проверка прав на отзыв
│   └── admin.py            # Админ-панель отзывов
│
├── static/                  # Статические файлы
│   ├── css/main.css        # Основные стили
│   ├── js/main.js          # JavaScript логика
│   └── images/             # Изображения
│
├── templates/               # HTML шаблоны
│   ├── base.html           # Базовый шаблон
│   ├── products/           # Шаблоны товаров
│   ├── orders/             # Шаблоны заказов
│   ├── users/              # Шаблоны пользователей
│   └── reviews/            # Шаблоны отзывов
│
├── media/                   # Загруженные файлы
│   └── product_images/     # Изображения товаров
│
├── manage.py               # Django management script
├── pyproject.toml          # Зависимости проекта
├── mypy.ini                # Конфигурация mypy
├── pytest.ini              # Конфигурация pytest
├── conftest.py             # Общие фикстуры для тестов
├── docker-compose.yml      # Docker Compose (PostgreSQL)
├── Dockerfile              # Docker образ для приложения
├── .env                    # Переменные окружения (не в git)
├── .env.example            # Пример переменных окружения
└── README.md               # Этот файл
```

## 🚀 Установка и запуск

### Вариант 1: Локальный запуск

#### 1. Клонируйте репозиторий
```bash
git clone https://github.com/32960/Online_Store_M3.git
cd Online_Store_M3
```

#### 2. Создайте виртуальное окружение
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows
```
#### 3. Установите зависимости
```bash
pip install -e .
```

#### 4. Настройте переменные окружения
Создайте файл .env в корне проекта (или скопируйте из .env.example):
```bash
cp .env.example .env
```
Отредактируйте .env и укажите ваши настройки:
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
POSTGRES_DB=hop_barley_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```
#### 5. Создайте базу данных PostgreSQL
```bash
# Создайте базу данных в PostgreSQL
createdb hop_barley_db
```
#### 6. Примените миграции
```bash
python manage.py migrate
```
#### 7. Создайте суперпользователя
```bash
python manage.py createsuperuser
```
#### 8. Загрузите тестовые данные (опционально)
```bash
python manage.py loaddata fixtures/initial_data.json
```
#### 9. Запустите сервер разработки
```bash
python manage.py runserver
```

Откройте браузер:

- **Сайт:** http://127.0.0.1:8000/
- **Админ-панель:** http://127.0.0.1:8000/admin/
- **Swagger UI:** http://127.0.0.1:8000/api/docs/
- **ReDoc:** http://127.0.0.1:8000/api/redoc/


### Вариант 2: Запуск через Docker

#### 1. Клонируйте репозиторий
```bash
git clone https://github.com/32960/Online_Store_M3.git
cd Online_Store_M3
```

#### 2. Настройте переменные окружения
```bash
cp .env.example .env
# Отредактируйте .env при необходимости
```

#### 3. Запустите Docker Compose
```bash
docker-compose up -d
```

#### 4. Примените миграции и создайте суперпользователя
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

Откройте браузер:

- **Сайт:** http://127.0.0.1:8000/
- **Админ-панель:** http://127.0.0.1:8000/admin/
- **Swagger UI:** http://127.0.0.1:8000/api/docs/

## 🔐 Переменные окружения

### Создайте файл .env в корне проекта:

```bash
# Django настройки
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=True

# PostgreSQL настройки
POSTGRES_DB=hop_barley_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Email настройки (для отправки уведомлений)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no_replace@hopandbarley.com
ADMIN_EMAIL=admin@hopandbarley.com

# JWT настройки
SIMPLE_JWT_ACCESS_TOKEN_LIFETIME=60
SIMPLE_JWT_REFRESH_TOKEN_LIFETIME=1440
```
**Важно:** Никогда не коммитьте .env в git! Файл уже добавлен в .gitignore.

## 📚 API документация

### Endpoints

#### Товары и категории
- `GET /api/products/` — список товаров (с фильтрацией, поиском, сортировкой)
- `GET /api/products/{slug}/` — детали товара
- `GET /api/categories/` — список категорий
- `GET /api/categories/{id}/` — детали категории

#### Заказы (требуется JWT)
- `GET /api/orders/` — список заказов пользователя
- `POST /api/orders/` — создать заказ
- `GET /api/orders/{id}/` — детали заказа
- `PUT /api/orders/{id}/` — обновить заказ
- `DELETE /api/orders/{id}/` — отменить заказ

#### Корзина
- `GET /api/cart/` — получить корзину
- `POST /api/cart/` — добавить товар
- `PATCH /api/cart/` — обновить количество
- `DELETE /api/cart/` — очистить корзину

#### Отзывы
- `GET /api/products/{id}/reviews/` — список отзывов
- `POST /api/products/{id}/reviews/` — создать отзыв (требуется JWT)

#### Аутентификация
- `POST /api/users/register/` — регистрация
- `POST /api/users/login/` — получить JWT токены
- `POST /api/users/refresh/` — обновить access токен

### Документация

- **Swagger UI:** `/api/docs/` — интерактивная документация
- **ReDoc:** `/api/redoc/` — альтернативный UI
- **OpenAPI схема:** `/api/schema/` — YAML/JSON схема

## 🛒 Корзина и сессии

### Как работает корзина

Корзина в проекте использует **сессионное хранилище Django** как для web-интерфейса, так и для REST API. Это означает, что корзина привязана к сессии пользователя, а не к его аккаунту.

### Web-интерфейс
В web-интерфейсе корзина работает через стандартные Django сессии:
1. **Добавление товара:** При добавлении товара в корзину, информация сохраняется в `request.session['cart']`
2. **Структура данных:**
```python
{
    "1": {"quantity": 2, "price": "14.99"},
    "3": {"quantity": 1, "price": "12.99"}
}
```
3. **Автоматическое обновление:** При изменении количества или удалении товара, сессия обновляется
4. **Оформление заказа:** При checkout корзина очищается после успешного создания заказа

### REST API

#### В REST API корзина также использует сессии, но с важными особенностями:
#### **Аутентификация через сессии**
#### Для работы с корзиной через API необходимо использовать **session-based аутентификацию:**
```bash
# 1. Получите CSRF токен и session cookie
curl -c cookies.txt -b cookies.txt http://127.0.0.1:8000/api/cart/

# 2. Добавьте товар в корзину
curl -X POST http://127.0.0.1:8000/api/cart/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -b cookies.txt \
  -d '{
    "product": 1,
    "quantity": 2
  }'

# 3. Получите содержимое корзины
curl -b cookies.txt http://127.0.0.1:8000/api/cart/
```

#### **Почему не JWT для корзины?**

**Причина:** Корзина должна работать для **неаутентифицированных пользователей**. Если бы корзина была привязана к JWT токену, пользователи не могли бы добавлять товары до регистрации/входа.

#### **Решение:**

#### **Примеры запросов**

#### **Добавить товар в корзину:**
```bash
# 1. Получите CSRF токен и session cookie
curl -X POST http://127.0.0.1:8000/api/cart/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -b cookies.txt \
  -d '{
    "product": 1,
    "quantity": 2
  }'
```

#### **Обновить количество:**
```bash
curl -X PATCH http://127.0.0.1:8000/api/cart/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -b cookies.txt \
  -d '{
    "product": 1,
    "quantity": 5
  }'
```

#### **Удалить товар из корзины:**
```bash
curl -X DELETE http://127.0.0.1:8000/api/cart/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -b cookies.txt \
  -d '{
    "product": 1
  }'
```

#### **Очистить корзину:**
```bash
curl -X DELETE http://127.0.0.1:8000/api/cart/clear/ \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -b cookies.txt
```

#### **Получить содержимое корзины:**
```bash
curl -b cookies.txt http://127.0.0.1:8000/api/cart/

# Ответ:
{
  "items": [
    {
      "product": {
        "id": 1,
        "name": "Citra Hops",
        "price": "14.99",
        "image": "/media/product_images/citra.jpg"
      },
      "quantity": 2,
      "total": "29.98"
    }
  ],
  "total_price": "29.98",
  "total_items": 2
}
```

### **Ограничения**
1. **Сессия истекает:** Если сессия истекает (по умолчанию 2 недели), корзина очищается
2. **Один браузер:** Корзина привязана к браузеру/устройству. На другом устройстве корзина будет пустой
3. **CSRF защита:** Все POST/PATCH/DELETE запросы требуют CSRF токен
4. **Нет синхронизации:** Если пользователь добавляет товары на разных устройствах, корзины не синхронизируются

### Альтернативный подход (не реализован)
Для production-проекта можно реализовать:

- **Гибридный подход:** Корзина в localStorage + синхронизация с сервером при входе 
- **База данных:** Корзина в localStorage + синхронизация с сервером при входе 
- **WebSocket:** Real-time синхронизация корзины между устройствами 

Но для учебного проекта сессионный подход полностью покрывает требования.

## 💡 Примеры запросов

### Регистрация
```bash
curl -X POST http://127.0.0.1:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password123"
  }'
```

### Получение JWT токенов
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "full_name": "John Doe",
    "phone": "+1234567890",
    "city": "New York",
    "shipping_address": "123 Main St",
    "payment_method": "debit",
    "items": [
      {"product": 1, "quantity": 2},
      {"product": 3, "quantity": 1}
    ]
  }'
```

### Создание заказа (с JWT)
```bash
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "full_name": "John Doe",
    "phone": "+1234567890",
    "city": "New York",
    "shipping_address": "123 Main St",
    "payment_method": "debit",
    "items": [
      {"product": 1, "quantity": 2},
      {"product": 3, "quantity": 1}
    ]
  }'
```

### Обновление access токена
```bash
curl -X POST http://127.0.0.1:8000/api/users/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

### Получение списка товаров с фильтрацией
```bash
curl "http://127.0.0.1:8000/api/products/?category__slug=hops&ordering=-price&search=citra"
```

## 🧪 Тестирование и линтеры

### Запуск тестов
```bash
python manage.py test
```

Ожидаемый результат:
```
105 passed in XX.XX s
```

### Запуск с покрытием
```bash
pytest --cov=. --cov-report=html
```

### Проверка типизации (mypy)
```bash
mypy .
```

##### Ожидаемый результат:
```
Success: no issues found in 41 source files
```

### Форматирование кода
```bash
# Black (автоматическое форматирование)
black .

# isort (сортировка импортов)
isort .

# flake8 (проверка стиля)
flake8 .
```
## ✅ Чек-лист реализации

### Основной функционал
- Каталог товаров с фильтрацией, поиском и сортировкой
- Детальная страница товара с техническими характеристиками
- Корзина с управлением количеством
- Оформление заказа с email-уведомлениями
- Регистрация и вход по email
- Личный кабинет с историей заказов
- Фильтрация заказов по статусу и дате
- Управление адресами (CRUD)
- Отзывы с рейтингом
- Автоматический пересчёт рейтинга товара

### REST API
- Endpoints для всех сущностей
- JWT аутентификация (access/refresh)
- Swagger UI и ReDoc
- Примеры запросов с JWT
- Описание схемы авторизации

### Качество кода
- Типизация всех файлов (mypy: 0 ошибок)
- Докстринги Google style для всех модулей
- Настроен mypy с django-stubs
- Переменные окружения через python-dotenv
- PostgreSQL вместо SQLite

### Инфраструктура
- Docker Compose для PostgreSQL
- .gitignore с правильными исключениями
- pyproject.toml с зависимостями
- README.md с полной документацией

## 📝 Лицензия
#### Этот проект создан в учебных целях


## 👤 Автор

**Андрей Зотеев**
#### GitHub: [@32960](https://github.com/32960)

**Примечание:** Проект разработан как учебное задание для демонстрации навыков работы с Django, REST API, JWT, PostgreSQL и современными инструментами разработки.

[Техническое задание.](Project_M3.md)