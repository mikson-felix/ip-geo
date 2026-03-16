# DEVELOPMENT_NOTES

## Implementation Walkthrough

I approached the implementation using a layered architecture and built the system incrementally from the core domain logic outward to infrastructure and API layers.

1. **Domain layer**

The first step was defining the core domain model and error taxonomy.
I introduced the `GeoInfo` entity and domain-specific exceptions to represent geolocation data and failure scenarios.
This layer is intentionally framework-agnostic and contains only business concepts.

2. **Application layer**

Next, I implemented the `GeoLookupUseCase`, which orchestrates the geolocation resolution workflow.
The use case coordinates three sources of data in order of increasing latency:

- Redis cache
- Local MaxMind database
- External geolocation providers

This structure ensures the fastest possible response path while minimizing external API usage.

3. **Infrastructure layer**

After the use case logic was stable, I implemented infrastructure integrations:

- Redis caching layer
- MaxMind GeoLite2 database repository
- HTTP clients for external providers (`ipapi.co`, `ip-api.com`)

To make external integrations resilient, I introduced:

- retry with exponential backoff
- per-provider rate limiting
- circuit breaker protection

These mechanisms protect the service from unstable upstream dependencies.

4. **API layer**

Finally, I implemented the FastAPI interface.

The API exposes two endpoints:

- `/health/` – service health check
- `/lookup/` – IP geolocation lookup

Response schemas and centralized exception handlers ensure consistent API responses.

5. **Dependency Injection**

Dishka was used to assemble application dependencies.
This keeps components loosely coupled and simplifies testing.

6. **Testing**

The project includes both:

- **unit tests** for domain logic and infrastructure components
- **integration tests** for API behavior

External services are mocked using `respx`, and Redis is simulated using `fakeredis`.

This approach allows validating behavior without requiring real external services.

---

## Total Time Spent

Approximately **5–6 hours**.

Rough breakdown:

- Architecture and project scaffolding — ~1 hour
- Core lookup logic and orchestration — ~1.5 hours
- External provider integration and resilience mechanisms — ~1 hour
- API implementation and error handling — ~45 minutes
- Testing — ~1 hour
- Documentation and cleanup — ~30–45 minutes

---

## Challenges & Solutions

### External provider reliability

External APIs can fail due to network issues, rate limits, or temporary outages.

**Solution**

Implemented several resilience mechanisms:

- retry with exponential backoff
- per-provider rate limiting
- circuit breaker pattern

This prevents cascading failures and protects the system from unstable dependencies.

---

### Optional local GeoIP database

The system should still function even if the MaxMind database file is missing.

**Solution**

The repository initialization gracefully handles missing or unreadable database files:

- logs a warning
- disables local lookup
- automatically falls back to external providers

This allows the service to run even when the local dataset is unavailable.

---

### Consistent error responses

FastAPI produces heterogeneous error responses by default.

**Solution**

Implemented centralized exception handlers that enforce a uniform error format:

```json
{
"code": "...",
"detail": "..."
}
```

This makes the API more predictable and easier to integrate with.

---

## GenAI Usage

AI tools were used primarily for:

- brainstorming architecture options
- validating design decisions
- generating documentation drafts

Core implementation, debugging, and architectural decisions were performed manually.

In some cases generated code required refactoring to match the layered architecture and ensure consistent project structure.

---

## API Design Decisions

The API was intentionally designed to be minimal and focused.

### Minimal endpoint surface

The service exposes only two endpoints:

- `/health/`
- `/lookup/`

This keeps the API surface small and easy to maintain.

---

### Query parameter for IP lookup

The lookup endpoint accepts the IP address as a query parameter:

```
GET v1/lookup/?ip=8.8.8.8
```


Reasons:

- aligns with typical lookup semantics
- easy to test using browsers and CLI tools
- avoids unnecessary request bodies

---

### Response transparency

The response includes metadata fields:

- source
- served_from_cache

This makes the response easier to debug and helps clients understand how the result was produced.

---

### Coordinate formatting

Coordinates are returned both as numeric values and formatted strings:

- latitude: float
- longitude: float
- latitude_formatted: string
- longitude_formatted: string

This preserves numeric precision while providing deterministic formatting for clients.

---

## Third-party API / Database Selection

### MaxMind GeoLite2

MaxMind GeoLite2 was selected because it is:

- an industry standard for IP geolocation
- regularly updated
- extremely fast for local lookups
- available as a free dataset

Using a local database also significantly reduces latency and dependency on external APIs.

---

### External providers

Two external services were used:

- **ipapi.co**
- **ip-api.com**

Reasons for choosing these providers:

- simple REST APIs
- good documentation
- no authentication required for basic usage
- widely used in similar services

Using multiple providers allows implementing fallback logic when one provider becomes unavailable.

---

### Redis

Redis was selected for caching because:

- extremely low latency
- simple key-value data model
- widely used in production for API caching

Caching responses reduces both latency and external API usage.

---

## Production Readiness

If this service were to be deployed to production, the next improvements would include:

1. **Metrics and monitoring**
   - Prometheus metrics for latency, cache hit rate, provider failures.

2. **Distributed tracing**
   - OpenTelemetry integration for request tracing.

3. **Request correlation**
   - request_id / correlation_id support in logs.

4. **Client rate limiting**
   - protection against abusive API usage.

5. **Negative caching**
   - caching "not found" results to avoid repeated external calls.

6. **Provider prioritization**
   - dynamic configuration of provider order.

7. **Configuration management**
   - stronger validation of provider settings.

8. **Docker support**
   - container image and docker-compose environment.

9. **CI pipeline**
    - automated linting, testing, and coverage checks.

10. **GeoIP dataset management**
    - automated download and update of MaxMind database.
