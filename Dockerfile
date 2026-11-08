FROM python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install -r requirements.txt
COPY prometheus_demo ./prometheus_demo
USER 65534:65534
EXPOSE 8000
CMD ["python", "-B", "-m", "prometheus_demo"]
