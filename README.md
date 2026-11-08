# FastAPI-приложение с метриками Prometheus

Самостоятельный пример XNova показывает путь от HTTP-запроса до результата PromQL. FastAPI-приложение отвечает кодами `200`, `404` и намеренным `500`, публикует Counter и Histogram на `/metrics`, а Prometheus опрашивает endpoint каждые пять секунд.

## Локальные проверки

Нужны Python 3.12 и Docker с Compose V2. Зависимости закреплены точными версиями.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m ruff format --check .
python -m ruff check .
python check_app.py
python -m pytest -q
```

В Windows PowerShell активируйте окружение командой `.venv\Scripts\Activate.ps1`. Детерминированная проверка должна завершиться строками:

```text
ok: status=200
not_found: status=404
controlled_error: status=500
metrics: counters=3 histogram=observed scrape_excluded=true
```

## Запуск стенда

```bash
docker compose config -q
docker compose up -d --build
docker compose ps
```

Приложение доступно по адресу `http://127.0.0.1:8000`, метрики — на `http://127.0.0.1:8000/metrics`, интерфейс Prometheus — на `http://127.0.0.1:9090`. Состояние цели находится на странице `http://127.0.0.1:9090/targets`.

Создайте контролируемый трафик:

```bash
for i in 1 2 3 4 5; do curl -sS http://127.0.0.1:8000/ > /dev/null; done
for i in 1 2; do curl -sS http://127.0.0.1:8000/error > /dev/null; done
```

В интерфейсе Prometheus выполните:

```promql
sum(rate(demo_http_requests_total[1m]))
sum(increase(demo_http_requests_total[1m]))
sum(rate(demo_http_requests_total{status=~"5.."}[1m]))
  / sum(rate(demo_http_requests_total[1m]))
```

Для отрицательного контроля остановите приложение, дождитесь следующего scrape и проверьте `up{job="python-app"}`: значение станет `0`. После запуска сервиса оно вернётся к `1`.

```bash
docker compose stop app
docker compose start app
docker compose down --volumes
```

## Структура

- `prometheus_demo/app.py` — фабрика FastAPI и middleware измерений;
- `prometheus_demo/routes.py` — HTTP-маршруты и `/metrics`;
- `prometheus_demo/metrics.py` — Counter, Histogram и ограниченные labels;
- `prometheus_demo/config.py` — настройки Uvicorn из окружения;
- `tests/` — pytest-контракты через `TestClient`;
- `compose.yaml` и `prometheus.yml` — локальный стенд.

Маршрут `/error` намеренно возвращает `500`. Стенд не реализует аутентификацию, TLS, долговременное хранение, алерты или высокую доступность и не предназначен для production-развёртывания.

Исходники распространяются по Apache-2.0; условия находятся в `LICENSE`.
