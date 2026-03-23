COMPOSE := docker compose

.PHONY: up down restart test test-cov lint check migrate migrate-new clean

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart api

test:
	uv run pytest -v

test-cov:
	uv run pytest --cov=app --cov-report=term-missing

lint:
	uv run pre-commit run --all-files

check: lint test test-cov

migrate-new:
	@read -p "Message: " msg; \
	$(COMPOSE) exec -T api alembic revision --autogenerate -m "$$msg"

migrate:
	$(COMPOSE) exec -T api alembic upgrade head

clean:
	$(COMPOSE) down -v --remove-orphans || true
	docker rmi $$(docker images -q --filter reference="$(COMPOSE_PROJECT_NAME)*") 2>/dev/null || true
	docker system prune -a --volumes -f
	rm -rf .venv .uv __pycache__ .mypy_cache .pytest_cache .ruff_cache .env .coverage htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
