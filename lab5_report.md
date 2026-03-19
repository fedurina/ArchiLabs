# Лабораторная работа №5
## Тема: Реализация архитектуры на основе сервисов (микросервисной архитектуры)
**Проект:** Система управления бронированиями и номерным фондом (high-end курорты/спа)

---

## 1) Реализация контейнеров и взаимодействия (Docker)

### 1.1. Контейнеры (минимум 3)
1. **frontend** — клиентская часть (Nginx + статический UI)  
2. **backend** — серверная часть (FastAPI)  
3. **db** — база данных (PostgreSQL)

### 1.2. Схема взаимодействия
- Пользователь открывает UI: `http://localhost:8080`
- **frontend** проксирует запросы `/api/v1/...` в **backend** по сети Docker: `http://backend:8000`
- **backend** читает/пишет данные в **db** (PostgreSQL) по сети Docker: `db:5432`

**Место под скриншот (docker compose ps):**  
<!-- TODO: screenshots/lab5/docker_compose_ps.png -->

**Место под скриншот (страница UI в браузере):**  
<!-- TODO: screenshots/lab5/ui_home.png -->

**Место под скриншот (Swagger или Postman):**  
<!-- TODO: screenshots/lab5/swagger_or_postman.png -->

---

## 2) Как запустить локально (инструкция)

### 2.1. Требования
- Docker Desktop

### 2.2. Запуск
В корне проекта выполнить:

```bash
docker compose up -d --build
```

Проверка:
- UI: `http://localhost:8080`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

Остановка:
```bash
docker compose down -v
```

---

## 3) Интеграционные тесты

Для интеграционных тестов используется Postman-коллекция + автотесты и запуск через Newman (в CI).

Файлы:
- `postman/Lab5_Hotel_API.postman_collection.json`
- `postman/Lab5_Docker.postman_environment.json`

**Место под скриншот (Postman Runner / Results):**  
<!-- TODO: screenshots/lab5/postman_runner_results.png -->

---

## 4) Непрерывная интеграция (CI)

Workflow: `.github/workflows/ci.yml`

Пайплайн выполняет:
1. `docker compose build` — сборка образов
2. `docker compose up -d` — запуск сервисов
3. ожидание `GET /health`
4. запуск интеграционных тестов (Newman + Postman коллекция)
5. остановка контейнеров

**Место под скриншот (GitHub Actions успешный прогон):**  
<!-- TODO: screenshots/lab5/github_actions_success.png -->
