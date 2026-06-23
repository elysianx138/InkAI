from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parents[1]
COMPOSE_FILE = BASE_DIR / "docker-compose.yml"

def _load_compose() -> dict:
    with  COMPOSE_FILE.open(encoding="utf-8") as handle:
        compose = yaml.safe_load(handle)

        assert isinstance(compose, dict)
        return compose
    
def _app_service(compose: dict) -> dict:
    service = compose["services"]["web"]

    assert isinstance(service, dict)
    return service

def test_docker_compose_builds_local_dockerfile():
    service = _app_service(_load_compose())

    assert service["build"]["context"] == "."

def test_docker_compose_maps_services_ports():
    service = _app_service(_load_compose())

    assert "8000:8000" in service["ports"]

def test_docker_compose_persists_mysql_data_volume():
    compose = _load_compose()

    assert "mysql_data" in compose["volumes"]

def test_mysql_maps_services_ports():
    compose = _load_compose()
    mysql_service = compose["services"]["mysql"]

    assert "3306:3306" in mysql_service["ports"]

def test_mysql_persists_database_password_and_volume():
    compose = _load_compose()
    mysql_service = compose["services"]["mysql"]
    environment = mysql_service["environment"]

    assert environment["MYSQL_ROOT_PASSWORD"] == "${MYSQL_ROOT_PASSWORD:-root123}"
    assert environment["MYSQL_DATABASE"] == "${MYSQL_DATABASE:-blog}"
    assert "./init.sql:/docker-entrypoint-initdb.d/init.sql" in mysql_service["volumes"]
    assert "mysql_data:/var/lib/mysql" in mysql_service["volumes"]

def test_redis_maps_services_ports():
    compose = _load_compose()
    redis_service = compose["services"]["redis"]

    assert "6379:6379" in redis_service["ports"]

