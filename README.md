# Kitchen Inventory

A self-hosted kitchen inventory and recipe management system. Scan barcodes, photograph receipts, import recipes by URL, and track what you have — displayed on a MagicMirror² wall display.

Built with FastAPI, PostgreSQL, and MagicMirror². Runs entirely in Docker with no cloud dependencies.

---

## Services

| Service | Port | Description |
|---|---|---|
| `api` | 8000 | FastAPI backend + REST API |
| `db` | 5432 | PostgreSQL database |
| `magicmirror` | 8080 | MagicMirror² frontend (browser preview or wall display) |

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
docker compose up
```

On first run this will:
- Pull the MagicMirror² image
- Build the API container
- Run database migrations and seed data automatically

### 4. Verify it's running

- **API docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MagicMirror preview**: [http://localhost:8080](http://localhost:8080)

---

## MagicMirror Configuration

The MagicMirror config is at [magicmirror/config/config.js](magicmirror/config/config.js). It is bind-mounted into the container so you can edit it directly without rebuilding.

Key setting:

```js
apiBaseUrl: "http://api:8000"  // Docker service name — works in any Compose stack
```

If you run MagicMirror outside Docker (e.g. bare Node.js on your Mac for development), change this to `http://localhost:8000`.

After editing the config, restart the container:

```bash
docker compose restart magicmirror
```

---

## Unraid Deployment

1. Clone or copy this repo to your appdata share, e.g. `/mnt/user/appdata/kitchen-inventory`
2. Copy `.env.example` to `.env` and fill in your keys
3. Set `RECEIPTS_HOST_PATH` to a persistent path, e.g. `/mnt/user/appdata/kitchen-inventory/receipts`
4. Run as a Compose stack via the Unraid Docker Compose manager, or SSH and run `docker compose up -d`
5. Point your MagicMirror display device's browser at `http://<unraid-ip>:8080`

Config files that persist on the host (no named volumes to hunt for):
- `.env` — credentials and paths
- `magicmirror/config/config.js` — MagicMirror layout and module settings
- `data/receipts/` (or your custom `RECEIPTS_HOST_PATH`) — receipt image archive

---

## Development

### Rebuild after code changes

```bash
docker compose down
docker compose build --no-cache   # only needed for structural/dependency changes
docker compose up
```

### Run tests

```bash
./run_tests.sh
# or
docker compose -f docker-compose.test.yml up --abort-on-container-exit
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

magicmirror/
  MMM-KitchenInventory/   MagicMirror² module
    MMM-KitchenInventory.js   Front-end (runs in browser/Electron)
    node_helper.js            Back-end (Node.js, talks to API)
  config/
    config.js               MagicMirror configuration (bind-mounted)
```

All inventory quantities are stored in base units (grams, ml, or count). Recipe ingredients are normalised to grams where possible to enable inventory-to-recipe matching without manual unit conversion.

---

## License

[MIT](LICENSE)
