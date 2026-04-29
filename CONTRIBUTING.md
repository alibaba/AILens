# Contributing to AI-Lens

Thank you for your interest in contributing! This document covers how to set up a development environment and submit changes.

## Development Setup

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| Java | **21+** |
| Maven | 3.6+ |
| Docker & Compose | latest |

> Note: Java 21 is required for the gateway. If your system default is older, set `JAVA_HOME` explicitly (see gateway step below).

### Gateway (Java)

Build and run with ClickHouse connection info:

```bash
cd gateway

# Build (required before first run)
JAVA_HOME=/path/to/jdk-21 mvn clean package -DskipTests -q

# Run
JAVA_HOME=/path/to/jdk-21 $JAVA_HOME/bin/java \
  -DCLICKHOUSE_URL="jdbc:clickhouse://<host>:8123/default" \
  -DCLICKHOUSE_USERNAME="<user>" \
  -DCLICKHOUSE_PASSWORD="<password>" \
  -jar gateway-server/target/gateway-server-*.jar
```

Run tests:

```bash
JAVA_HOME=/path/to/jdk-21 mvn test
```

### Backend (Python)

> **Important:** run from the **monorepo root**, not from `backend/`. The package uses relative imports.

```bash
# From monorepo root
pip3 install -r backend/requirements.txt

TRACEQL_BASE_URL=http://localhost:8080 \
  python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run tests (also from monorepo root):

```bash
cd backend && pytest
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev       # dev server on :3000
npm test -- --run # Vitest unit tests
npm run build     # production build check
```

### Start everything at once (backend + frontend)

```bash
./scripts/dev.sh
# Gateway must be started separately — it requires ClickHouse credentials
```

## Pull Request Guidelines

1. **Fork** the repository and create your branch from `main`.
2. **Describe** what your PR does and why in the PR description.
3. **Tests** — add or update tests to cover your change.
4. **Lint** — make sure existing tests pass before opening a PR.
5. **Small PRs** — prefer focused, reviewable changes over large rewrites.

### Commit message style

```
type(scope): short summary

Optional longer description.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Examples:
```
feat(backend): add cross-experiment comparison endpoint
fix(frontend): correct p99 latency chart axis label
docs: update quick-start instructions
```

## Reporting Issues

- Use the issue tracker at https://github.com/alibaba/AILens/issues.
- For bugs: include steps to reproduce, expected vs. actual behavior, and environment info.
- For features: describe the use case and the value it adds.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating you agree to abide by its terms.

## License

By contributing you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
