FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY pipelines ./pipelines
COPY warehouse ./warehouse
COPY apps ./apps
COPY seeds ./seeds
COPY seed.py ./
RUN pip install --no-cache-dir .
ENV PYTHONUNBUFFERED=1
EXPOSE 4000
CMD ["python", "-m", "catalog_api"]
