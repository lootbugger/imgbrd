# imgbrd

A lightweight imageboard inspired by 4chan — create boards, post threads, reply with images/files, and manage content with per-thread poster IDs.

Built with FastAPI, SQLite, Jinja2, and HTMX.

## Features

- Multiple boards, each with its own thread listing
- Create threads with title, body, name, and file attachments
- Reply to threads with body, name, and files (HTMX-powered, no page reload)
- Supports any file type — images (with lightbox viewer), video, audio, and download links
- **Poster IDs** — each user gets a deterministic per-thread hash; same person = same ID within a thread, changes across threads
- Cookie-based ownership — only the poster who created a post can delete it
- Soft delete — replies show `[deleted by ...]`, threads redirect to the board view
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
uv run uvicorn main:app --reload
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
├── main.py              # FastAPI app, route handlers, middleware
├── models.py            # SQLAlchemy models (Board, Post, Image)
├── schemas.py           # Pydantic schemas (BoardIn/Out, PostIn/Out, ImageOut)
├── database.py          # SQLAlchemy engine and session dependency
├── alembic.ini          # Alembic configuration
├── imgbrd/              # Alembic migration files
│   ├── env.py
│   └── versions/
├── templates/           # Jinja2 templates
│   ├── boards.html      # List of all boards
│   ├── board_posts.html # Thread listing for a board
│   ├── thread.html      # Thread view with replies
│   ├── _board.html      # Board card partial
│   ├── _post.html       # Post/reply partial (OP and replies)
│   ├── _reply_form.html # HTMX reply form fragment
│   ├── _file.html       # File type detection and rendering
│   └── 404.html         # Custom 404 page
├── static/              # Static assets
│   └── style.css        # Styles
└── uploads/             # Uploaded files directory
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

## Hosting

Local network: run with `--host 0.0.0.0` to access from other devices on your WiFi.

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

For access from anywhere, try [Tailscale](https://tailscale.com) or [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/).
