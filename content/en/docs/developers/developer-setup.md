---
title: "Captua — Developer setup"
linkTitle: "Developer setup"
url: /docs/developers/developer-setup/
translationKey: docs-developers-developer-setup
docs_section: developers
---

This page sets up a development environment for Captua, so that every contributor works against the same stack. For branches, pull requests and releases, see [Git workflow](/docs/developers/git-workflow/). For the camera libraries behind each backend, see [Camera libraries](/docs/developers/camera-libraries/). The backend's endpoints are described in the [API reference](/docs/developers/api-reference/).

## Required software {#required-software}

You need these tools on any operating system:

- **Git**
    - Check whether Git is installed with `git --version`.
    - If it is not installed:
        - macOS: `brew install git` (or the Xcode command line tools)
        - Windows: download it from the [official Git website](https://git-scm.com/download/win)
        - Linux (Debian and derivatives): `sudo apt install git`
- **Docker Desktop**
    - macOS: download it from [Docker's official site](https://docs.docker.com/desktop/install/mac-install/)
    - Windows: download it from [Docker's official site](https://docs.docker.com/desktop/install/windows-install/)
    - Linux: install Docker Engine (`curl -fsSL https://get.docker.com | sh`) and the `docker compose` plugin.
    - After installing, run `docker --version` and `docker compose version` to check the installation.

The development stack runs in Docker images that contain Node and Python, so a development machine needs nothing else. The native backend on a Raspberry Pi is the exception: it runs under [pixi](https://pixi.sh) (see [Option 2](#option-2-raspberry-pi-mode-with-cameras)).

## Cloning the repository {#cloning-the-repository}

Clone the repository with its submodules:

```bash
git clone --recurse-submodules git@github.com:UCSB-AMPLab/digitization-toolkit-software.git
cd digitization-toolkit-software
```

The submodules are addressed over SSH, so the clone needs an SSH key registered with GitHub.

The checkout has this structure:

```text
.
├── backend                 # FastAPI backend (submodule)
├── frontend                # SvelteKit frontend (submodule)
├── wiki                    # project wiki (submodule)
├── docs
├── scripts                 # start, setup, update and provisioning scripts
├── docker-compose.yml      # base stack: database, production frontend, optional backend
├── docker-compose.dev.yml  # development overlay: Vite dev server
├── docker-compose.pi.yml   # appliance overlay: appliance paths and Nginx
├── .env.example
├── nginx.conf
├── CHANGELOG.md
├── CITATION.cff
├── VERSION
├── LICENSE
├── README.md
└── README-SETUP.md
```

## Create the environment file {#create-the-environment-file}

The backend service reads `.env` (`env_file: ./.env` in `docker-compose.yml`). The file is not in the repository and `scripts/start-dev.sh` does not create it, so Docker Compose stops if it is missing. Create it from the example before the first start:

```bash
cp .env.example .env
```

`.env.example` sets `APP_ENV=dev`. In a development environment with no `BOOTSTRAP_TOKEN` set, the first administrator account can be created without a token (`_authorize_bootstrap` in `backend/app/api/auth.py`). Outside development, Captua asks for the token.

## Start the services {#start-the-services}

Captua runs in two arrangements:

- **Database and frontend** run in Docker containers.
- **Backend** runs natively on a Raspberry Pi, for camera access, or in Docker, for development.

### Option 1: Development mode (no cameras) {#option-1-development-mode-no-cameras}

From the root of the repository, run:

```bash
./scripts/start-dev.sh
```

On Windows, use `scripts\start-dev.bat` or `scripts\start-dev.ps1`.

The script runs this Docker Compose command, which you can also run directly:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile with-backend up --build
```

The `docker-compose.dev.yml` overlay is required for the Vite dev server. Without it, the base `docker-compose.yml` builds and serves the **production** frontend image on port 3000 instead.

This command:

- starts the **database** (PostgreSQL 16, from a pinned image, on port 5432, bound to 127.0.0.1)
- builds and starts the **backend** (FastAPI and Uvicorn, port 8000), which applies the database migrations (`alembic upgrade head`) before it starts
- builds and starts the **frontend** (SvelteKit and Vite, port 5173)
- mounts your local `backend/` and `frontend/` directories in the containers, so changes reload live

### Option 2: Raspberry Pi mode (with cameras) {#option-2-raspberry-pi-mode-with-cameras}

On a unit provisioned with `scripts/setup.sh`, the systemd service `dtk.service` runs the stack through `scripts/start.sh`. Do not start a second copy by hand. Stop the service first (`sudo systemctl stop dtk`) if you need to run the backend yourself.

`scripts/setup.sh` prepares a unit: it creates `.env` if it is missing, installs pixi v0.73.0 if no pixi is installed (the committed `pixi.lock` needs a pixi that reads lock-file format v7), installs the backend environment, links the system camera libraries, builds python-gphoto2 against the system libgphoto2, and applies the database migrations. On an unprovisioned Pi, run `scripts/setup.sh`, or do the backend steps by hand:

```bash
# from the repository root: start PostgreSQL and wait until it is healthy
docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d --pull never --wait db
cd backend
pixi install --locked        # first time only
pixi run setup-camera-link   # puts the system picamera2 and libcamera packages on the environment's path
pixi run db-upgrade          # applies the migrations; the backend refuses to start against an un-migrated database
cd ..
```

`setup-camera-link` needs the Raspberry Pi OS packages `python3-picamera2` and `python3-libcamera`, which `scripts/setup.sh` installs. pixi supports only `linux-aarch64` and `linux-64` (`platforms` in `backend/pixi.toml`), so the native backend cannot run on macOS or Windows. Use the Docker backend there.

From the repository root, start the database, the production frontend and Nginx, as `scripts/start.sh` does:

```bash
docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d --pull never --wait --remove-orphans
```

In a separate terminal, start the native backend:

```bash
cd backend
pixi run dev     # Uvicorn with --reload, for development on the Pi
```

`pixi run dev` starts the FastAPI backend with `--reload`, listening on `0.0.0.0:8000`. The appliance itself runs `pixi run start`, which is the same server without `--reload`.

Captua detects cameras when they are first used, not at startup. At startup, the backend checks the `CAMERA_BACKEND` value and refuses to start if it names no backend this build has (`assert_camera_backend_configured` in `backend/capture/service.py`).

**Why native?** Camera access needs Raspberry Pi system libraries (libcamera and picamera2, libgphoto2, and USB access for CHDK bodies) that are difficult to reproduce in Docker. There is no `run_backend_native.sh` script and no Python virtualenv to activate. pixi manages the backend's dependencies.

## Verify the backend {#verify-backend}

Open `http://localhost:8000/health` in your browser. The response is:

```json
{"status": "ok"}
```

## Verify the frontend {#verify-frontend}

In development mode, open `http://localhost:5173`. On a Pi, open `http://localhost` or `http://captua.local`. Nginx serves Captua on port 80 there, and nothing listens on 5173.

The root address redirects to the welcome page, or to the dashboard if a user is already signed in. On the welcome page, choose **Get started in English**. On a new database, Captua then opens the setup page, where you create the administrator account. Otherwise it opens the login page.

## Common issues {#common-issues}

- **Port already in use**: if ports 5432, 8000 or 5173 are occupied, stop the conflicting services or change the ports. Ports 5432 and 8000, and the production frontend's 3000, are set in `docker-compose.yml`. The development frontend's 5173 is set in `docker-compose.dev.yml`.
- **The frontend cannot reach the backend**:
    - Check that the backend is running: `curl http://localhost:8000/health`.
    - For the native backend, check that `.env` has `DATABASE_HOST=localhost`. The Docker backend uses `db`, which `docker-compose.yml` sets itself.
- **Camera not detected**: camera access needs the native backend on a Raspberry Pi. The Docker backend cannot reach cameras.
- **Backend stops at startup**: an invalid `CAMERA_BACKEND` value, or a database that has not been migrated, stops the backend before it serves requests. Correct the value in `.env`, or run `pixi run db-upgrade`.
- **Live reloading does not work**: restart the containers:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile with-backend down
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile with-backend up --build
```

For the native backend:

```bash
# Stop it with Ctrl+C, then restart
cd backend && pixi run dev
```

## Shut everything down {#shut-everything-down}

When you finish, stop the containers:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile with-backend down
```

You can also stop and start the containers from Docker Desktop.
