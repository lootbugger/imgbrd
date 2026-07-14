# imgbrd

A lightweight imageboard inspired by 4chan - create boards, post threads, reply with images/files, and manage content with per-thread poster IDs.

Built with FastAPI, SQLite, Jinja2, and HTMX.

## Features

- Multiple boards, each with its own thread listing
- Create threads with title, body, name, and file attachments
- Reply to threads with body, name, and files (HTMX-powered, no page reload)
- Supports any file type - images (with lightbox viewer), video, audio, and download links
- **Poster IDs** - each user gets a deterministic per-thread hash; same person = same ID within a thread, changes across threads
- Cookie-based ownership - only the poster who created a post can delete it
- Soft delete - replies show `[deleted by ...]`, threads redirect to the board view
- SimpleLightbox for full-screen image viewing
- Mobile-friendly

## Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Jinja2 templates, HTMX, SimpleLightbox
- **Migrations**: Alembic

## Setup

```bash
# Install dependencies
uv sync

# Create the database
uv run alembic upgrade head

# Run the server
uv run uvicorn src.main:app --reload
```

Open http://127.0.0.1:8000/boards in your browser.

### Database

The database file is `database.db` (SQLite). To reset:

```bash
rm database.db && uv run alembic upgrade head
```

### Project structure

```
imgbrd/
├── src/                      # Application code
│   ├── main.py               # FastAPI app setup
│   ├── database.py           # Engine, session, Base
│   ├── templates.py          # Jinja2Templates singleton
│   ├── middleware.py         # Poster token cookie middleware
│   ├── exceptions.py         # HTTP exception handler
│   ├── boards/               # Board domain
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── service.py
│   │   ├── dependencies.py
│   │   └── router.py
│   └── posts/                # Post domain
│       ├── models.py
│       ├── schemas.py
│       ├── service.py
│       ├── dependencies.py
│       └── router.py
├── imgbrd/                   # Alembic migration files
│   ├── env.py
│   └── versions/
├── templates/                # Jinja2 templates
├── static/                   # Static assets
├── uploads/                  # Uploaded files directory
├── alembic.ini
└── pyproject.toml
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/boards` | List all boards (HTML) |
| POST | `/boards` | Create a board (JSON) |
| DELETE | `/boards/{id}` | Delete a board and all its posts |
| GET | `/boards/{id}/posts` | List threads in a board (HTML) |
| POST | `/boards/{id}/posts` | Create a new thread (form, redirects) |
| GET | `/boards/{id}/posts/{pid}` | View thread with replies (HTML) |
| POST | `/boards/{id}/posts/{pid}/reply` | Reply to a thread (HTMX fragment) |
| DELETE | `/boards/{id}/posts/{pid}` | Delete a post (cookie auth required) |

## TODO

- [ ] Docker - containerize for easy deployment
- [ ] Async DB - switch to async SQLAlchemy

## Hosting

Local network: run with `--host 0.0.0.0` to access from other devices on your WiFi.

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

For access from anywhere, try [Tailscale](https://tailscale.com) or [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/).
