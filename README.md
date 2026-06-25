# Creative Studio

A collection of creative modules built with Flask and Python. Each module runs as an independent service, integrated through a proxy into a single Flask application.

---

## Table of Contents

- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Setup](#setup)
  - [Clone the repository](#1-clone-the-repository)
  - [Main Flask app virtual environment](#2-main-flask-app-virtual-environment)
  - [Environment variables](#3-environment-variables)
  - [Each service has its own virtual environment](#4-each-service-has-its-own-virtual-environment)
  - [Install Node.js dependencies](#5-install-nodejs-dependencies)
- [Running in Development](#running-in-development)
  - [Start everything with one command](#start-everything-with-one-command)
  - [Run services individually](#run-services-individually)
- [Database Setup](#database-setup)
- [Running in Production](#running-in-production)
- [Features](#features)
- [Coming Soon](#coming-soon)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)

---

## Requirements

- **Python 3.12+** (recommended) — 3.13 works with some patches (see service notes)
- **Node.js** (18+ recommended) and npm
- *(Optional)* **Nix** package manager — if you prefer using flakes

---

## Project Structure

```
.
├── flaskr/
│   ├── auth/               # Authentication (login, register, email)
│   ├── errors/             # Custom error handlers
│   ├── explore/            # Explore page (public artworks)
│   ├── gallery/            # User gallery (CRUD for artworks)
│   ├── main/               # Main routes (home, landing)
│   ├── modules/            # Proxy routes for each service
│   ├── profile/            # User profile (avatar, cover, about)
│   ├── static/             # CSS, JavaScript, images
│   ├── templates/          # Jinja2 HTML templates
│   ├── models.py           # SQLAlchemy models
│   └── utils.py            # Helper functions (file upload, etc.)
├── services/
│   ├── zelija/             # Pixel art grid builder (Pygbag)
│   ├── sablier/            # Generative hourglass (Pygbag)
│   ├── aquarium/           # Procedural aquarium (Pygbag)
│   ├── neural_transfer/    # Neural style transfer (TensorFlow Hub)
│   ├── image_processing/   # Image filters & effects (OpenCV, Pillow)
│   └── data_visualization/ # Data art from CSV (Matplotlib, Pandas)
├── uploads/                # User-uploaded files (avatars, artworks)
├── logs/                   # Application logs
├── migrations/             # Alembic database migrations
├── .env                    # Environment variables
├── requirements.txt        # Main Flask app dependencies
├── package.json            # npm scripts (dev, buildcss, etc.)
├── studio.py               # Flask application entrypoint
└── README.md               # This file
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/frost-rvl/creative-studio.git
cd creative-studio
```

### 2. Main Flask app virtual environment

Create a Python virtual environment and install the main dependencies.

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment variables

Copy the example environment file and fill in your values.

```bash
cp .env.example .env
```

Edit `.env` with your own settings. Here is a description of each variable:

**`SECRET_KEY`**
A strong, random string used for cryptographic signing (session, tokens). Generate one with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**`MAIL_SERVER`**
The SMTP server for sending emails. For Gmail, use: `smtp.gmail.com` (also works with `smtp.googlemail.com`).

**`MAIL_PORT`**
Typically `587` for TLS, or `465` for SSL. `587` is recommended.

**`MAIL_USE_TLS`**
Set to `1` to enable TLS (recommended) or `0` to disable.

**`MAIL_USERNAME`**
The email address you send from (e.g., `your-app@gmail.com`).

**`MAIL_PASSWORD`**
The app password or account password. For Gmail, you must use an "App Password" if 2FA is enabled.

**`ADMINS`**
A comma-separated list of email addresses that will receive error notifications when the app fails.

Example `.env` file:

```env
SECRET_KEY="a-very-secret-key-generated-with-the-command-above"
MAIL_SERVER="smtp.gmail.com"
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME="your-app@gmail.com"
MAIL_PASSWORD="your-app-password"
ADMINS="admin1@example.com,admin2@example.com"
```

### 4. Each service has its own virtual environment

For each service that runs as a separate Flask or Pygbag application, you need to create a virtual environment inside its folder and install its dependencies.

#### Neural Transfer (TensorFlow style transfer)

```bash
cd services/neural_transfer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Download the style reference images (run once):

```bash
cd style_transfer
python download_styles.py
deactivate
cd ../..
```

> **Note:** The first run may take a while because TensorFlow Hub downloads the model (~100 MB).

#### Image Processing (OpenCV filters)

```bash
cd services/image_processing
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..
```

#### Data Visualization (Matplotlib, Pandas)

```bash
cd services/data_visualization
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

*(Optional)* Generate a sample CSV dataset for testing:

```bash
python generate_sample_data.py
```

```bash
deactivate
cd ../..
```

#### Pygbag-based services (Zelija, Sablier, Aquarium)

These services are built with Pygbag and do not require a separate virtual environment — they are bundled as `.pygbag` archives and run with the main Python environment. Make sure `pygbag` is installed globally or in the main virtual environment (it is included in `requirements.txt`).

### 5. Install Node.js dependencies

```bash
npm install
```

This installs:

- **Tailwind CSS** (for styling)
- **Browser-sync** (for live reload)
- **concurrently** (to run multiple processes in parallel)

---

## Database Setup

Make sure your main virtual environment is active before running these commands:

```bash
source .venv/bin/activate
```

**First time setup** — initialize the schema and seed the artwork types:

```bash
flask db upgrade      # run all migrations (creates tables)
flask seed_db         # seed artwork types (zelija, sablier, aquarium, etc.)
```

**Reset the database** — drops all tables, recreates them, and re-seeds:

```bash
flask reset_db
flask seed_db
```

**Initialize without migrations** — creates all tables directly from models (use only if you have no migrations yet):

```bash
flask init_db
flask seed_db
```

> **Note:** `seed_db` is safe to run multiple times — it skips artwork types that already exist.

---

## Running in Development

### Start everything with one command

```bash
npm run dev
```

This launches:

| Service            | Port | Description                          |
|--------------------|------|--------------------------------------|
| Main Flask app     | 5000 | The core application                 |
| Tailwind CSS       | —    | Watches and compiles CSS             |
| Browser-sync       | 3000 | Live-reload proxy (optional)         |
| Zelija             | 8000 | Pixel art grid builder (Pygbag)      |
| Sablier            | 8001 | Generative hourglass (Pygbag)        |
| Neural Transfer    | 8002 | Style transfer API (Flask)           |
| Aquarium           | 8003 | Procedural aquarium (Pygbag)         |
| Image Processing   | 8004 | Image effects API (Flask)            |
| Data Visualization | 8005 | Data art API (Flask)                 |

All services are proxied through the main Flask app, so you only need to open [http://localhost:5000](http://localhost:5000) (or the Browser-sync URL at [http://localhost:3000](http://localhost:3000)) to access them.

### Run services individually

If you need to run a specific service on its own (e.g., for debugging):

**Main Flask app:**
```bash
flask run
```

**Neural Transfer:**
```bash
cd services/neural_transfer
source .venv/bin/activate
python service.py
```

**Image Processing:**
```bash
cd services/image_processing
source .venv/bin/activate
python service.py
```

**Data Visualization:**
```bash
cd services/data_visualization
source .venv/bin/activate
python service.py
```

**Pygbag services:**
```bash
pygbag services/zelija
pygbag services/sablier
pygbag services/aquarium
```

> **Note:** Pygbag services run on ports 8000, 8001, and 8003 by default. The main Flask app proxies them via `/pygbag/`, `/sablier/`, `/aquarium/` respectively.

---

## Running in Production

Build the CSS once (no watcher in prod):

```bash
npx tailwindcss -i ./flaskr/static/css/input.css -o ./flaskr/static/css/output.css
```

Then start all services with Gunicorn:

```bash
npm run prod
```

This launches Gunicorn with 4 workers instead of the Flask dev server. Debug mode is off, auto-reloader is disabled, and error emails are active.

| Service            | Port | Description                     |
|--------------------|------|---------------------------------|
| Main app (Gunicorn)| 5000 | 4 workers, no debugger          |
| Zelija             | 8000 | Pixel art grid builder (Pygbag) |
| Sablier            | 8001 | Generative hourglass (Pygbag)   |
| Aquarium           | 8003 | Procedural aquarium (Pygbag)    |
| Neural Transfer    | 8002 | Style transfer API (Flask)      |
| Image Processing   | 8004 | Image effects API (Flask)       |
| Data Visualization | 8005 | Data art API (Flask)            |

> **Note:** For real internet-facing production, put Nginx or Caddy in front of Gunicorn as a reverse proxy to handle HTTPS, static files, and load balancing.

---

## Features

### User System

- Registration, login, logout
- Email verification (with token)
- Password reset (via email)
- User profile with avatar and cover images
- Edit profile (about me, username, email)
- Following system — see artworks from people you follow

### Artwork Management

- Create artworks from any module (saved as PNG images)
- Private / Public visibility toggle
- Delete artworks
- Gallery page to view your own artworks
- Explore page to browse public artworks from all users

### Creative Modules

| Module             | Description                                                                 | Technology                    |
|--------------------|-----------------------------------------------------------------------------|-------------------------------|
| Zelija             | Interactive grid builder — place shapes, rotate, resize           | Pygbag (Python + Pygame)      |
| Sablier            | Generative hourglass simulation with real-time physics and sand particles   | Pygbag (Python + Pygame)      |
| Aquarium           | Procedural aquarium with fish, bubbles, animated seaweed, and colour palettes | Pygbag (Python + Pygame)    |
| Neural Transfer    | Apply artistic styles (Van Gogh, Munch, Picasso) to your photos             | TensorFlow Hub + Flask        |
| Image Processing   | Apply filters, distortions, and geometric transforms                        | OpenCV + Pillow + Flask       |
| Data Visualization | Upload any CSV and turn it into an expressive, artistic visualisation       | Matplotlib + Pandas + Flask   |

Each module is accessible from the Modules page and integrated with the main save-to-gallery workflow.

---

## Coming Soon

- Full-text search for artworks (title, description, username)
- Artwork description translator (using a translation API)
- User notifications (follows, likes, comments)
- Comment and like system on public artworks

---

## Contributing

Feel free to open issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Acknowledgements

- Built with [Flask](https://flask.palletsprojects.com/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)
- Icons from [Lucide](https://lucide.dev/)
- [Pygbag](https://pygame-web.github.io/) for running Pygame in the browser
- [TensorFlow Hub](https://tfhub.dev/) for the style transfer model
- [Unsplash](https://unsplash.com/) for sample images

---

*Happy creating!*