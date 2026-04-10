
ifneq ($(shell which docker-compose 2>/dev/null),)
    DOCKER_COMPOSE := docker-compose
else
    DOCKER_COMPOSE := docker compose
endif

.PHONY: env check-secrets install remove start startAndBuild stop update up down logs ps smoke

ENV_FILE ?= .env

env:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)

check-secrets:
	@chmod +x scripts/check-no-secrets.sh
	@./scripts/check-no-secrets.sh

install: up

up: env check-secrets
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) up -d --build --remove-orphans

remove:
	@chmod +x confirm_remove.sh
	@./confirm_remove.sh

start: env
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) start
startAndBuild: 
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) up -d --build --remove-orphans

down:
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) down --remove-orphans

stop:
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) stop

logs:
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) logs -f open-webui

ps:
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) ps

smoke:
	@chmod +x scripts/smoke.sh
	@set -a; . $(ENV_FILE); set +a; ./scripts/smoke.sh

update:
	# Calls the LLM update script
	chmod +x update_ollama_models.sh
	@./update_ollama_models.sh
	@git pull
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) down
	# Make sure the ollama-webui container is stopped before rebuilding
	@docker stop open-webui || true
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) up --build -d
	$(DOCKER_COMPOSE) --env-file $(ENV_FILE) start
