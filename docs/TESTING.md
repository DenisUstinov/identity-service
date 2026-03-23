# API Testing

## Конфигурация

```bash
export BASE_URL="http://localhost:8000/api/v1"
```

## Эндпоинты

### GET /health

```bash
curl -s "$BASE_URL/health"
```

### POST /auth/register

```bash
# Успешная регистрация (200)
curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"StrongPass123!"}'
```

```bash
# Дубликат email (400)
curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"AnotherPass123!"}'
```

```bash
# Некорректный email (422)
curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid","password":"Pass123!"}'
```

```bash
# Слабый пароль (422)
curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123"}'
```

### POST /auth/login

```bash
# Успешный вход (200) — получить токен
curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"StrongPass123!"}'
```

```bash
# Сохранить токен в переменную (для последующих запросов)
export TOKEN=""
```

```bash
# Неверный пароль (400)
curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"WrongPass"}'
```

### GET /auth/me

```bash
# Доступ с токеном (200)
curl -s "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

```bash
# Без токена (401)
curl -s "$BASE_URL/auth/me"
```

```bash
# С просроченным токеном (401)
curl -s "$BASE_URL/auth/me" \
  -H "Authorization: Bearer <EXPIRED_TOKEN>"
```

## Проверка базы данных (Docker)

```bash
# users — последние 10 записей
docker exec identity-postgres-1 psql -U postgres -d identity_db \
  -c "SELECT id, email, is_active, is_verified, created_at \
      FROM users \
      ORDER BY id DESC LIMIT 10;"

# Сводка: количество пользователей
docker exec identity-postgres-1 psql -U postgres -d identity_db \
  -c "SELECT 'users' as table_name, COUNT(*) FROM users;"
```

## Тестирование полного флоу (CI + Deploy)

```bash
# Ветка → CI → если ок → тег → Deploy
git checkout -b temp/full-test
git commit --allow-empty -m "WIP: full test"
git push -u origin temp/full-test
git tag v0.0.1-test
git push origin v0.0.1-test

# Откатить всё после проверки
git push origin --delete temp/full-test
git tag -d v0.0.1-test
git push origin --delete v0.0.1-test
git reset --soft HEAD~1
git checkout main
git branch -d temp/full-test
```

```bash
sudo ./svc.sh install ubuntu
sudo ./svc.sh start
sudo ./svc.sh status
journalctl -u actions.runner.identity-service -f
```
