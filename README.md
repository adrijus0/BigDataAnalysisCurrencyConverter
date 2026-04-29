# Currency Converter API

A Flask-based currency converter API that fetches live exchange rates from the [Frankfurter API](https://api.frankfurter.app), which is publicly available, requires no API key, and is backed by the European Central Bank — so the rates are the same ones used by banks across the EU. The whole app runs inside a Docker container so you don't need Python installed locally to run it.

## Installation and Usage

### 1. Install Docker

You need either:

- Docker Desktop (Windows/macOS), or
- Docker Engine (Linux)

No local Python is required — everything runs inside the container.

---

### 2. Pull the image from Docker Hub

The image is publicly available on Docker Hub:

https://hub.docker.com/repository/docker/adrijus0/currency-converter/general

```bash
docker pull adrijus0/currency-converter:latest
```

Image: `adrijus0/currency-converter:latest`

---

### 3. Run the container

```bash
docker run -p 5000:5000 adrijus0/currency-converter:latest
```

The `-p 5000:5000` maps port 5000 on your machine to port 5000 inside the container. The API will be available at http://localhost:5000.

---

### 4. Verify the service is running

```bash
curl "http://localhost:5000/health"
```

```json
{"service": "currency-converter", "status": "ok"}
```

---

## Build The Image From Source

If you'd rather build the image from source:

```bash
# from the currency-converter directory
docker build -t adrijus0/currency-converter:latest .
docker run -p 5000:5000 adrijus0/currency-converter:latest
```

### Pushing to Docker Hub

This is how I pushed the image up after building it:

```bash
docker login
docker push adrijus0/currency-converter:latest
```

---

## Stopping the Container

```bash
docker ps
docker stop <container-id>
```

---

## Table of Contents

- [Installation and Usage](#installation-and-usage)
  - [1. Install Docker](#1-install-docker)
  - [2. Pull the image from Docker Hub](#2-pull-the-image-from-docker-hub)
  - [3. Run the container](#3-run-the-container)
  - [4. Verify the service is running](#4-verify-the-service-is-running)
- [Build It Yourself](#build-it-yourself)
  - [Pushing to Docker Hub](#pushing-to-docker-hub)
- [Stopping the Container](#stopping-the-container)
- [API Endpoints](#api-endpoints)
  - [`/health`](#health)
  - [`/currencies`](#currencies)
  - [`/rates`](#rates)
  - [`/convert`](#convert)
  - [Error Responses](#error-responses)
- [Project Structure](#project-structure)
- [Why I Set Up the Dockerfile This Way](#why-i-set-up-the-dockerfile-this-way)
- [Challenges & Notes](#challenges--notes)
- [What I Would Add Next](#what-i-would-add-next)

---

## API Endpoints

| Method | Path | Parameters | Description |
|--------|------|-----------|-------------|
| GET | `/health` | — | Health check |
| GET | `/currencies` | — | List all supported currencies |
| GET | `/rates` | `base` (required) | Get all exchange rates for a base currency |
| GET | `/convert` | `amount`, `from`, `to` (all required) | Convert an amount between two currencies |

---

### `/health`

Returns the service status. Useful for confirming the container is up and the Flask app is responding.

Example:

```bash
curl "http://localhost:5000/health"
```

```json
{"service": "currency-converter", "status": "ok"}
```

---

### `/currencies`

Returns the full list of currencies supported by the Frankfurter API (around 30 entries).

Example:

```bash
curl "http://localhost:5000/currencies"
```

```json
{
  "currencies": {
    "AUD": "Australian Dollar",
    "EUR": "Euro",
    "USD": "US Dollar"
  }
}
```

*(truncated — Frankfurter actually returns ~30 currencies)*

---

### `/rates`

Returns all exchange rates for the given base currency on the latest available date.

#### `base`
The base currency code. Required.

Example:

```bash
curl "http://localhost:5000/rates?base=EUR"
```

```json
{"base": "EUR", "date": "2025-04-25", "rates": {"AUD": 1.72, "GBP": 0.86, "USD": 1.08}}
```

```bash
curl "http://localhost:5000/rates?base=USD"
```

```json
{
  "base": "USD",
  "date": "2025-04-25",
  "rates": {
    "EUR": 0.923,
    "GBP": 0.789
  }
}
```

---

### `/convert`

Converts an amount between two currencies using the latest available exchange rate.

#### `amount`
The numeric amount to convert. Required.

#### `from`
Source currency code. Required.

#### `to`
Target currency code. Required.

Example:

```bash
curl "http://localhost:5000/convert?amount=250&from=USD&to=EUR"
```

```json
{"amount": 250.0, "date": "2025-04-25", "from": "USD", "result": 230.75, "to": "EUR"}
```

```bash
curl "http://localhost:5000/convert?amount=100&from=USD&to=EUR"
```

```json
{
  "amount": 100.0,
  "date": "2025-04-25",
  "from": "USD",
  "result": 92.3,
  "to": "EUR"
}
```

---

### Error Responses

If a required parameter is missing:

```bash
curl "http://localhost:5000/convert?amount=100&from=USD"
```

```json
{"error": "Missing required query parameter: to"}
```

If an invalid currency code is provided:

```bash
curl "http://localhost:5000/rates?base=XYZ"
```

```json
{"error": "invalid currency", "detail": "XYZ is not a supported currency"}
```

---

## Project Structure

| File | What it does |
|------|-------------|
| `app.py` | The main Flask app with all the API routes |
| `Dockerfile` | Instructions for building the Docker image |
| `requirements.txt` | Python packages the app needs |
| `.dockerignore` | Tells Docker what files to ignore when building |
| `README.md` | This file |

---

## Why I Set Up the Dockerfile This Way

- I used `python:3.11-slim` instead of just `python` because the full image is over 1GB and the slim version has everything Flask needs at a fraction of the size.
- I copy `requirements.txt` and run pip *before* copying `app.py`. This means if I only change the Python code, Docker doesn't reinstall all the packages — it reuses the cached layer from the previous build. I read about Docker layer caching and this was the main thing that made rebuilds faster.
- The `--no-cache-dir` flag stops pip from saving downloaded packages inside the image, which keeps it smaller.
- I added `.dockerignore` so Docker doesn't copy the README and other files that aren't needed to actually run the app.

---

## Challenges & Notes

One thing that caught me out with Docker: I kept editing `app.py` and wondering why my changes weren't showing up when I tested the container. Turns out you have to rebuild the image every time you change the code — the container doesn't pick up changes automatically. Once I understood that the container is basically a snapshot of the code at build time it made sense, but it wasn't obvious at first.

---

## What I Would Add Next

- Add some kind of caching so it doesn't call the Frankfurter API on every single request (ECB rates only update once a day so there's no point hitting the API constantly)
