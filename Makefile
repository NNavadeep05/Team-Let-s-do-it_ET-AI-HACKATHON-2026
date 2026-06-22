.PHONY: up down migrate seed bootstrap list

list:
	@echo "Available targets:"
	@echo "  up        - Start all database containers (Postgres, Neo4j, Qdrant, MinIO, Redis)"
	@echo "  down      - Shut down containers and remove volumes"
	@echo "  migrate   - Run SQLAlchemy/Alembic database migrations"
	@echo "  seed      - Seed Neo4j ontology and load the demo dataset"
	@echo "  bootstrap - Clean install, run migrations, constraints, ontology seed, qdrant, minio, and demo load"

up:
	docker compose up -d postgres neo4j qdrant minio redis

down:
	docker compose down -v

migrate:
	docker compose exec -T api alembic upgrade head

seed:
	docker compose exec -T api cypher-shell -u neo4j -p neuronpass -f /ontology/constraints.cypher || true
	docker compose exec -T api cypher-shell -u neo4j -p neuronpass -f /ontology/seed.cypher || true
	docker compose exec -T api python /infra/qdrant_init.py
	docker compose exec -T api python /infra/minio_init.py
	docker compose exec -T api python /seed/load_demo.py

bootstrap:
	docker compose down -v
	docker compose up -d postgres neo4j qdrant minio redis
	@echo "Waiting for services to be healthy..."
	@sleep 15
	docker compose exec -T api alembic upgrade head
	docker compose exec -T api cypher-shell -u neo4j -p neuronpass -f /ontology/constraints.cypher || true
	docker compose exec -T api cypher-shell -u neo4j -p neuronpass -f /ontology/seed.cypher || true
	docker compose exec -T api python /infra/qdrant_init.py
	docker compose exec -T api python /infra/minio_init.py
	docker compose exec -T api python /seed/load_demo.py
