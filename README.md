# IP Geolocation Service

A FastAPI-based microservice that resolves geolocation information for a given IP address.

The service first attempts to resolve the location using a **local MaxMind GeoLite2 database**, then falls back to **external providers** if the local database has no data or is unavailable.

Results are cached in **Redis** to reduce latency and external API usage.

---

## Features

- FastAPI async API
- Local GeoIP lookup via **MaxMind GeoLite2**
- Fallback to external providers
  - ipapi.co
  - ip-api.com
- Redis caching (15 minutes)
- Retry policy for external providers
- Rate limiting per provider
- Circuit breaker protection
- Structured JSON logging (`structlog`)
- Graceful degradation when MaxMind DB is missing
- Dependency Injection via **Dishka**
- Centralized exception handling
- OpenAPI documentation
- 90%+ test coverage
- Pre-commit hooks (ruff, mypy)

---

## Architecture

The project follows a layered architecture.



app/
| ├──api/ # FastAPI routes and schemas
| ├── application/ # Use cases
| ├── domain/ # Entities, exceptions, interfaces
| ├── infrastructure/ # Redis, MaxMind, HTTP providers
| ├── ioc/ # Dependency injection configuration
| ├── config.py # Application settings
└── main.py # FastAPI application entrypoint

### Request flow

request
│
▼
Redis cache
│
├── hit → return cached result
│
▼
MaxMind GeoLite2 database
│
├── hit → cache + return
│
▼
External providers
│
├── retry
├── rate limit
├── circuit breaker
│
▼
cache + return

---

## API

### Health check

GET /health/

Response

```json
{
  "status": "ok"
}
```

### IP lookup
GET /lookup/?ip=8.8.8.8

Response
```json
{
  "ip": "8.8.8.8",
  "country": "United States",
  "country_code": "US",
  "city": "Mountain View",
  "region": "California",
  "latitude": 37.386,
  "longitude": -122.0838,
  "latitude_formatted": "37.386000",
  "longitude_formatted": "-122.083800",
  "source": "maxmind",
  "served_from_cache": false
}
```

### Error format

All errors use a unified format.

```json
{
  "code": "invalid_ip",
  "detail": "Invalid IP address"
}
```

### Example errors:

__HTTP code__

- 422 invalid_ip
- 404 geo_not_found
- 502 external_service_error
- 500 internal_server_error

## Configuration

All configuration is provided via environment variables.

See .env.example.

__Example:__

- cp .env.example .env

**Important variables:**

*Variable Description:*

* REDIS_URL Redis connection string
* GEOIP_DB_PATH MaxMind GeoLite2 DB path
* CACHE_TTL_SECONDS Cache lifetime
* LOG_LEVEL Logging level
* LOG_JSON JSON logs

## Running locally

1. Install dependencies

```bash
make install
```

2. Run Redis

```bash
docker run -p 6379:6379 redis:7
```

3. Run application

```bash
make run
```

## API docs will be available at:

http://localhost:8000/docs

### Running tests

```bash
make test
```

### With coverage:

```bash
make cov
```

## Pre-commit

### Install hooks:

```bash
make precommit-install
```

### Checks include:

* ruff (lint + format)

* mypy (type checking)

## Design decisions

* MaxMind DB is optional

__If the local database file is missing, the service will:__

* log a warning

* skip local lookup

* fallback to external providers

This allows the service to run without local GeoIP data.

### External provider protection

#### __External APIs are protected using:__

* retry with exponential backoff

* rate limiting

* circuit breaker

This prevents cascading failures and protects upstream services.

__Caching__

Results are cached in Redis for 15 minutes to reduce latency and external API calls.

## Tech stack

* FastAPI

* httpx

* Redis

* structlog

* Dishka (dependency injection)

* respx (HTTP mocking)

* pytest

* fakeredis (Redis testing)

## Possible improvements

* request tracing

* metrics (Prometheus)

* GeoIP ASN lookup

* IPv6-specific optimizations

* provider priority configuration

* negative caching for unknown IPs

## License

MIT
