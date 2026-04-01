# Kitchen Inventory

A self-hosted kitchen inventory and recipe management system. Scan barcodes, photograph receipts, import recipes by URL, and track what you can cook — displayed on a tablet-first touch UI.

Built with FastAPI, PostgreSQL, React + Vite. Runs entirely in Docker with no cloud dependencies.

---

## Services

| Service | Port | Description |
|---|---|---|
| `api` | 8000 | FastAPI backend + REST API |
| `db` | 5432 | PostgreSQL database |
| `frontend` | 3000 | React + Vite UI (tablet-first, touch input) |

---

## Quick Start

### 1. Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac/Windows/Linux) or Docker + Docker Compose on a server/Unraid
- API keys (see step 2)

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

| Variable | Required | Where to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes — receipt scanning | [console.anthropic.com](https://console.anthropic.com) |
| `SPOONACULAR_API_KEY` | Yes — recipe import | [spoonacular.com/food-api](https://spoonacular.com/food-api) |
| `USDA_API_KEY` | Yes — ingredient weights | [fdc.nal.usda.gov](https://fdc.nal.usda.gov/api-guide.html) |
| `RECEIPTS_HOST_PATH` | No | Path on the host where receipt images are stored. Defaults to `./data/receipts` |
| `TZ` | No | Your timezone, e.g. `Europe/London`. Defaults to `America/New_York` |

### 3. Start everything

```bash
docker-compose up
```

On first run this will:
- Build the API and frontend containers
- Run database migrations and seed data automatically

### 4. Verify it's running

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **API docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Unraid Deployment

1. Clone or copy this repo to your appdata share, e.g. `/mnt/user/appdata/kitchen-inventory`
2. Copy `.env.example` to `.env` and fill in your keys
3. Set `RECEIPTS_HOST_PATH` to a persistent path, e.g. `/mnt/user/appdata/kitchen-inventory/receipts`
4. Run as a Compose stack via the Unraid Docker Compose manager, or SSH and run `docker-compose up -d`
5. Point your tablet or display browser at `http://<unraid-ip>:3000`

Config files that persist on the host (no named volumes to hunt for):
- `.env` — credentials and paths
- `data/receipts/` (or your custom `RECEIPTS_HOST_PATH`) — receipt image archive

---

## Development

### Access the database (psql)

**Locally:**
```bash
docker-compose exec db psql -U admin -d inventory
```

**On Unraid (via SSH):**
```bash
docker exec -it kitchen-inventory-db-1 psql -U admin -d inventory
```

Replace `admin` and `inventory` with the values from your `.env` (`POSTGRES_USER` / `POSTGRES_DB`).

### Rebuild after code changes

```bash
docker-compose down
docker-compose build --no-cache   # only needed for structural/dependency changes
docker-compose up
```

### Run tests

```bash
docker-compose -f docker-compose.test.yml run --rm test-runner
```

### API documentation

Interactive Swagger UI is available at [http://localhost:8000/docs](http://localhost:8000/docs) whenever the stack is running.

---

## Architecture

```
app/
  api/v1/       API endpoints (versioned)
  crud/         Database operations
  schemas/      Pydantic models
  models/       SQLAlchemy models
  config/       Alias seeds, substitution seeds, fresh weights

frontend/
  src/
    pages/      Page components
    api/        API client functions
    interfaces/ TypeScript types
```

All inventory quantities are stored in base units (grams, ml, or count). Recipe ingredients are normalised to grams where possible to enable inventory-to-recipe matching without manual unit conversion.

---

## License

[MIT](LICENSE)
