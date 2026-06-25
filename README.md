# Creative Studio

A collection of projects built with Python.

## Requirements
- Python 3.x
- Node.js & npm
- (Optional) Nix package manager

## Installation

### 1. Set up a Python virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install python dependencies

Using pip

```bash
pip install -r requirements.txt
```

then setup your .env with the given example

Or using Nix

```bash
nix develop
```

then setup your .envrc and add "use flake" to load flake automatically

### 3. Install Node.js dependencies

```bash
npm install
```

## Run (Development)

To start the developent environment:

```bash
npm run dev
```

This will launch flask, tailwindcss(builder) and browser-sync

## Features
- Landing page
- User authentication
- Email support 
- User profile page
- Artwork modules
- Gallery/Explore/Home pages

## Coming son
- Full text search
- Artwork description translator
- User notifications
