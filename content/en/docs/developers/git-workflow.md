---
title: "Captua — Git workflow"
linkTitle: "Git workflow"
url: /docs/developers/git-workflow/
translationKey: docs-developers-git-workflow
docs_section: developers
---

This page describes how Captua's repositories use Git: branches, pull requests, submodule pointers and releases, across the superproject and its submodules. To set up the development stack, see [Developer setup](/docs/developers/developer-setup/).

## Repository structure {#repository-structure}

- **Superproject** (`UCSB-AMPLab/digitization-toolkit-software`): holds the orchestration (`docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.pi.yml`, `nginx.conf`), the environment example (`.env.example`), the setup, update, rollback and provisioning scripts and systemd units in `scripts/`, the documentation, `CHANGELOG.md`, `VERSION`, and the submodule pointers.
- **Submodules**:
    - `frontend/`: the SvelteKit application (`UCSB-AMPLab/digitization-toolkit-frontend`)
    - `backend/`: the FastAPI application (`UCSB-AMPLab/digitization-toolkit-backend`)
    - `wiki/`: the project wiki (`UCSB-AMPLab/digitization-toolkit-software.wiki`)

Most code changes are made in the submodule repositories. The superproject records which commit of each submodule belongs together.

## Team branching model {#team-branching-model}

What the three repositories actually do (checked against their branches, merged pull requests and protection settings on 2026-11-08):

- **Branches.** Work branches from `dev` and is named after the repository area: `frontend/<topic>` and `backend/<topic>` in the submodules; `chore/bump-<topic>`, `docs/<topic>` or `scripts/<topic>` in the superproject.
- **Into dev.** Every change reaches `dev` through a pull request; `dev` and `main` refuse direct pushes, force-pushes and deletions. No approving review is required. Before merging: CI passes where the repository has it (backend: `pytest -m "not camera"` and the migration drift check; frontend: `npm run check` and Vitest; the superproject has none), and `codex review --base origin/dev` reports nothing open. Pull requests are merged with a merge commit (`gh pr merge --merge`), never squashed or rebased.
- **Submodule pointers.** After a submodule pull request merges, a superproject branch `chore/bump-<topic>` moves the pointer to the merged commit, and its own pull request goes into `dev`.
- **Releases.** A release is a `dev`→`main` pull request in each submodule and then in the superproject, merged by an administrator with a merge commit. The protection rule asks for one approving review on `main`; administrators are exempt (`enforce_admins` is off), and release merges have used that exemption. Only the superproject is tagged, without a `v` prefix (`0.2.0`), with a CHANGELOG pull request, a `release: Captua <version>` commit and a GitHub Release. Docker images are built on each unit by `scripts/update.sh`, not by CI.
- **Urgent fixes.** A few fixes have gone straight to `main` as `fix/<topic>` pull requests.

```text
frontend/<topic>, backend/<topic>  ──PR──►  dev  ──release PR──►  main
chore/bump-<topic> (superproject)  ──PR──►  dev
```

## Continuous integration {#continuous-integration}

No status check is required by the branch protection on any of the three repositories, so a pull request can be merged with CI failing. Check the result before merging.

| Repository | Workflow | When it runs | What it runs |
|---|---|---|---|
| backend | `.github/workflows/ci.yml` | pull requests into `dev`, pushes to `dev` | `pixi run -e dev pytest tests/ -m "not camera"`, then `pixi run -e dev db-check-drift` |
| frontend | `.github/workflows/ci.yml` | every pull request, pushes to `dev` and `main` | `npm ci`, `npm run check`, `npx vitest run` (in Chromium, through Playwright) |

The superproject has no workflow.

## Workflow for submodules {#workflow-for-submodules}

### 1. Prepare the checkout {#prepare-checkout}

```bash
git fetch --all
git switch dev
git pull origin dev
git submodule update --init --recursive   # takes the exact pins the superproject records (no --remote)
```

### 2. Create a feature branch in a submodule {#create-a-feature-branch}

```bash
cd frontend
git checkout dev
git pull origin dev
git checkout -b frontend/capture-panel
```

Commit as you work, then push:

```bash
git push -u origin frontend/capture-panel
```

### 3. Open a pull request in the submodule repository {#open-a-pr-in-the-submodule}

Open the pull request against `dev`. Merge it with a merge commit once CI passes (see [Team branching model](#team-branching-model)).

### 4. Update the superproject pointer {#update-the-superproject-pointer}

A code change lands in two steps:

1. **Land the change in the submodule first.** Branch inside the submodule (`frontend/<topic>` or `backend/<topic>`), open a PR against that submodule's repo, merge it.
2. **Bump the superproject pointer.** On a superproject branch `chore/bump-<topic>` from `dev`, advance the submodule to the merged commit, commit the new gitlink, and open a PR into `dev`.

After the submodule pull request merges:

```bash
cd ..
git switch dev
git pull origin dev
git switch -c chore/bump-<topic>
git -C frontend fetch origin                 # or backend
git -C frontend checkout <merged-sha>        # the exact commit merged in the submodule PR
                                             # (read it with: git -C frontend rev-parse --short HEAD)
git add frontend
git commit -m "chore(submodule): bump frontend to <short-sha>"
git push -u origin chore/bump-<topic>
```

Open a pull request from `chore/bump-<topic>` into `dev` in the superproject. Do not push the commit to `dev` directly: `dev` refuses direct pushes.

## Commit guidelines {#commit-guidelines}

Commits follow [Conventional Commits](https://www.conventionalcommits.org/), with a scope. Keep each commit to one change:

- `feat(api): add /upload endpoint`
- `fix(ui): handle 404 from /health`
- `chore(submodule): bump frontend to <short-sha>`

## Pull request checklist {#pull-request-checklist}

- [ ] The stack builds and runs in Docker (`./scripts/start-dev.sh`)
- [ ] Backend CI and frontend CI pass on the pull request
- [ ] `codex review --base origin/dev` reports nothing open
- [ ] Commit messages are meaningful
- [ ] No unresolved merge conflicts
- [ ] Documentation updated if needed

## Working with Docker {#working-with-docker}

On a development machine, the stack runs in Docker, and you do not need Node.js or Python installed locally. On a Raspberry Pi the backend runs natively under pixi, and the backend's CI runs its tests under pixi as well (see [Developer setup](/docs/developers/developer-setup/#option-2-raspberry-pi-mode-with-cameras)).

- Start the stack:

  ```bash
  ./scripts/start-dev.sh
  ```

  This runs `docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile with-backend up --build`. A plain `docker compose up --build` builds the production frontend on port 3000 and does not start the backend, which is in the `with-backend` profile.
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000/health`

### Switching branches {#switching-branches}

- If only source files changed, `git checkout <branch>` is enough.
- If the frontend's dependencies changed (`package.json` or `package-lock.json`), restart the stack. The development frontend runs `npm install` each time it starts (`command` in `docker-compose.dev.yml`), which brings the `frontend_node_modules` volume in line with `package-lock.json`. If the packages still look wrong after a restart, stop the stack, remove that volume, and start again:

  ```bash
  docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile with-backend down
  docker volume rm dtk_frontend_node_modules
  ./scripts/start-dev.sh
  ```

  The volume name has the Compose project name `dtk` (`name:` in `docker-compose.yml`) as its prefix.
- If the backend's dependencies changed (`requirements.txt`, which moves together with `pixi.toml` and `pixi.lock`), `./scripts/start-dev.sh` rebuilds the backend image with `--build`.

{{< callout type="warning" appearance="simple" >}}
Do not use `docker compose down -v` to refresh dependencies. `-v` removes the `postgres_data` volume, which deletes the development database. Without the development overlay, the same command also leaves `frontend_node_modules` in place, because only `docker-compose.dev.yml` declares that volume.
{{< /callout >}}
