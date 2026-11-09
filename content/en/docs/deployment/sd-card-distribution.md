---
title: "SD Card Distribution"
url: /docs/deployment/sd-card-distribution/
translationKey: docs-deployment-sd-card-distribution
docs_section: deployment
source: docs/developers/sd_card_distribution.qmd
---

***

This guide explains how to prepare and ship a Raspberry Pi SD card image with Captua pre-installed, so the recipient can plug it in and access the application from any device on the same network — without any manual IP configuration.

---

## How It Works {#how-it-works}

The Raspberry Pi broadcasts its hostname over the local network using **mDNS** (via the Avahi daemon, pre-installed on Raspberry Pi OS). This means any device on the same network can reach the Pi at `http://<hostname>.local` without knowing its IP address. Every unit is called `captua`, so it answers at `http://captua.local`.

The browser calls the API at `/api` on the page's own origin, and Nginx on port 80 passes it to the backend. The name therefore matters only for finding the unit: opening it by its IP address works the same, and so does any other name that reaches it.

---

## Preparing the Master Image {#preparing-the-master-image}

### 0. Install Captua on the master card {#install-captua-on-the-master-card}

Flash **Raspberry Pi OS (Legacy, 64-bit) Lite**, Debian 12 "Bookworm": it is the system Captua is tested on. Raspberry Pi Imager's plain "Raspberry Pi OS Lite (64-bit)" entry now installs Debian 13 "Trixie", which Captua has not been validated against. In Imager's customisation options, set the username to `pi`: `scripts/dtk.service` runs the service as `pi` from `/home/pi/dtk`, and the kiosk installer expects the same user. Set up the network and SSH there as well (see [What the Recipient Needs to Do](#what-the-recipient-needs-to-do)).

Then, on the Pi, as `pi`, with an internet connection:

```bash
sudo apt update && sudo apt install -y git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and back in, so that the `pi` account is in the `docker` group, then continue:

```bash
curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=v0.73.0 bash
git config --global url."https://github.com/".insteadOf "git@github.com:"
git clone --recurse-submodules https://github.com/UCSB-AMPLab/digitization-toolkit-software.git ~/dtk
cd ~/dtk
sudo ./scripts/setup.sh
sudo ./scripts/install-service.sh
sudo systemctl start dtk
curl http://localhost:8000/health   # {"status":"ok"}
curl -I http://localhost            # HTTP 200, the interface through nginx
sudo ./scripts/installkb.sh
sudo ./scripts/install-kiosk-service.sh
```

- The `git config` line comes before the clone because `.gitmodules` registers the submodules over SSH (`git@github.com:`), and the Pi has no GitHub key: the line makes git fetch them over HTTPS. The repositories are public, so the clone needs no token.
- pixi is pinned to the version in `PIXI_VERSION` in `scripts/setup.sh`: older versions cannot read the committed `pixi.lock`.
- `setup.sh` creates `.env` from `.env.example`, builds the frontend image, installs the backend environment, names the unit (step 1), and applies the database migrations. It needs the internet; the card does not need it afterwards.
- `install-service.sh` installs and enables `dtk.service` and `dtk-secrets.service`, but does not start `dtk`; `systemctl start` does, and the two `curl` lines check that the backend and the interface answer.
- `installkb.sh` and `install-kiosk-service.sh` set up the kiosk: the full-screen browser on the display attached to the Pi.

### 1. Name the unit {#name-the-unit}

`setup.sh` names the unit `captua` (step 6f, `scripts/provision-hostname.sh`): it sets the hostname and the `127.0.1.1` line of `/etc/hosts`, and sets `HOST_IP=captua.local` and adds `http://captua.local` to `CORS_ORIGINS` in `.env`. Nothing needs editing by hand.

Two units on one network cannot share a name. For the second unit at such a site, give it its own name when running setup:

```bash
sudo CAPTUA_HOSTNAME=captua-2 ./scripts/setup.sh
```

`setup.sh` still accepts the older name `DTK_HOSTNAME`.

Verify:

```bash
hostname
# captua
grep -E '^(HOST_IP|CORS_ORIGINS)=' /home/pi/dtk/.env
```

### 2. Confirm Avahi is running {#confirm-avahi-is-running}

Avahi (mDNS) is pre-installed on Raspberry Pi OS. Confirm it is active:

```bash
systemctl is-enabled avahi-daemon
systemctl is-active avahi-daemon
```

Both should return `enabled` / `active`. If not:

```bash
sudo systemctl enable --now avahi-daemon
```

### 3. Verify {#verify}

Open `http://captua.local` from another device on the same network, and the unit's IP address too: both load the app.

`HOST_IP` and `CORS_ORIGINS` no longer route anything on the appliance. The frontend reads `PUBLIC_API_BASE=/api` at runtime (`docker-compose.pi.yml`), and `HOST_IP` sets only SvelteKit's `ORIGIN`. Both are kept correct for the code a rollback can restore, whose frontend calls `http://${HOST_IP}/api`.

### 4. Image the SD card {#image-the-sd-card}

Once the system is working correctly, shut down the Pi cleanly and create an image of the SD card from another computer.

In the examples below, replace `/dev/sdX` or `/dev/diskN` with the card's whole device, not a partition. Check the path before continuing.

**Linux**

Identify the card with `lsblk` and unmount any mounted partitions on it. Then create the image:

```bash
lsblk
sudo dd if=/dev/sdX of=dtk-master.img bs=4M status=progress
```

**macOS**

Identify the card with `diskutil list`, unmount its volumes, and create the image:

```bash
diskutil list
diskutil unmountDisk /dev/diskN
sudo dd if=/dev/diskN of=dtk-master.img bs=4m
```

Once `dd` finishes successfully, eject the card:

```bash
diskutil eject /dev/diskN
```

**Windows**

Use [Win32 Disk Imager](https://sourceforge.net/projects/win32diskimager/). Select the card's device, enter `dtk-master.img` as the destination file, and click **Read**. Check that you selected the correct card.

{{< callout type="tip" title="Shrink the image before compressing it" >}}
Tools such as [PiShrink](https://github.com/Drewsif/PiShrink) can shrink the `.img` file by removing unused filesystem space from the image. If you want to do this, work on the uncompressed image.
{{< /callout >}}

After creating the image and, if applicable, shrinking it, compress it:

```bash
gzip dtk-master.img
```

The result is `dtk-master.img.gz`. On Windows, you can use a compression tool that supports gzip.

{{< callout type="note" title="Secrets are per-unit — imaging is safe at any point" >}}
`SECRET_KEY`, `DATABASE_PASSWORD`, and `BOOTSTRAP_TOKEN` (the token for creating the first account) are regenerated automatically on each physical unit by `dtk-secrets.service` (installed by `install-service.sh`). It records the Pi's hardware serial in `/var/lib/dtk/secrets-provenance`; when a flashed clone boots on a different Pi, the serial mismatch triggers fresh secrets before the backend starts — including rotating the Postgres password inside the cloned data directory. You do **not** need to scrub secrets from the master image, and test-booting the master before imaging is fine.
{{< /callout >}}

{{< callout type="warning" title="Never add a credential to `.env` by hand" >}}
The per-unit generation above covers `SECRET_KEY`, `DATABASE_PASSWORD`, and `BOOTSTRAP_TOKEN`. It does not cover anything you add yourself while preparing a card — and whatever sits in `.env` at imaging time is copied into every clone of that image. A card has been found with a live GitHub personal access token in plaintext in `~/dtk/.env`; nothing in the software put it there.

Provisioning never needs a token: the repositories are public, so you clone them over HTTPS with no token, and `setup.sh` makes later submodule fetches use HTTPS as well. If a private fetch is ever required, read the token from a prompt so it never appears on the command line, then clear it:

```bash
read -rs -p "Token: " GH_TOKEN && export GH_TOKEN
gh repo clone UCSB-AMPLab/<repo>
unset GH_TOKEN
```

Do **not** pass it inline as `GH_TOKEN=… gh …`: that writes the token verbatim into `~/.bash_history`, which sits on the card and is copied into the image along with everything else. For the same reason, never embed a token in a remote URL — it persists in `.git/config` and travels with the image.

Before imaging a master card, diff `.env` against `.env.example`: it should carry no keys the template does not have.
{{< /callout >}}

{{< callout type="warning" title="Provision the offsite copy and accounts on each unit, not on the master" >}}
Everything else on the card is copied into every clone as well, and the per-unit generation does not change it:

- `/var/lib/dtk/offsite.env` and `/var/lib/dtk/rclone.conf`, which `provision-rclone.sh` writes when it is given a unit's offsite key or Fisqua token. `setup.sh` already runs it without key material; give it none on the master, and provision each unit's offsite copy after flashing, as in [Updating a Unit, step 4](/docs/deployment/updating-a-unit/#provision-the-offsite-copy-without-restarting).
- The database, with every account created during a test boot. Create no accounts on the master.

From the release after 0.2.0, a card that has been started before its offsite copy is provisioned is in "Scanner only" mode, and so is every clone of it. Set the mode on each unit once its offsite copy is provisioned ([Updating a Unit, 6.2a](/docs/deployment/updating-a-unit/#set-the-units-mode)).
{{< /callout >}}

---

## Flashing and Delivering the Image {#flashing-and-delivering-the-image}

On Linux, write the image to a new SD card. Check that `/dev/sdX` is the destination card: **this step erases its contents**. Unmount any mounted partitions on the destination card.

```bash
gzip -dc dtk-master.img.gz | sudo dd of=/dev/sdX bs=4M status=progress
sync
```

On macOS and Windows, or as an alternative on Linux, open Raspberry Pi Imager, choose the option to use a local image, and select `dtk-master.img.gz`. Select the destination card and write the image.

---

## What the Recipient Needs to Do {#what-the-recipient-needs-to-do}

Nothing, in most cases. They:

1. Insert the SD card and power on the Pi.
2. Connect the Pi to their local network (Ethernet or Wi-Fi configured before imaging).
3. Open `http://captua.local` from any browser on the same network.

{{< callout type="note" title="Wi-Fi pre-configuration" >}}
If the destination uses Wi-Fi (not Ethernet), configure the network credentials on the SD card **before** shipping.

Raspberry Pi OS Bookworm replaced `dhcpcd` + `wpa_supplicant` with NetworkManager, so dropping a `wpa_supplicant.conf` on the `/boot` partition **no longer works** — Bookworm ignores that file.

- **When preparing the master card from Raspberry Pi OS:** set the Wi-Fi SSID and password in Raspberry Pi Imager's customisation options, under **Wi-Fi**. Also enable SSH under **Remote Access**, preferably with public-key authentication.
- **On an already prepared card:** configure Wi-Fi through NetworkManager, for example with `sudo nmcli device wifi connect "<SSID>" password "<password>"`, or add a NetworkManager keyfile connection profile under `/etc/NetworkManager/system-connections/`.

Do not assume Imager can apply the same customisation options to a cloned local image. Configure the network and SSH on the master card before creating the image. Without SSH, you cannot provision the unit remotely without a display: a fresh Raspberry Pi OS Lite installation has SSH disabled by default, and you will then need a keyboard and display to get in.
{{< /callout >}}

---

## Troubleshooting {#troubleshooting}

**`captua.local` doesn't resolve**

- Check that the Pi and your computer are on the same network and that Avahi is active on the Pi.
- Try pinging: `ping captua.local`
- As a fallback, find the IP via the router's DHCP client list and open it directly: the app works by IP.

**A unit in service before 0.1.0-beta answers as `digitool.local`**

Units set up before 0.1.0-beta were called `digitool`. `update.sh` renames them to `captua` and keeps `digitool.local` answering; 0.2.0 still does (see [Updating a unit](/docs/deployment/updating-a-unit/#the-unit-name-digitool-becomes-captua)).

**CORS errors in the browser**

The browser calls the API on the page's own origin, so the production stack has no cross-origin calls and this error should not occur there. On the development stack (Vite on `:5173` calling the backend on `:8000`), the page's origin must be in `CORS_ORIGINS` in `.env`; update that list and restart the backend. The page and the API must also be on the same site, because the session cookie is `SameSite=Strict`: open the page on `localhost` when `PUBLIC_API_BASE` names `localhost`, and on `127.0.0.1` when it names `127.0.0.1`. With a mismatch the browser shows no CORS error: the backend answers the login with 200 and refuses the next request with 401. The [API reference, CORS Configuration](/docs/developers/api-reference/#cors-configuration), has the details.

**Two Pis on the same network**

mDNS hostnames must be unique per network. Name the second unit at setup with `CAPTUA_HOSTNAME=captua-2` (step 1). On a unit already set up, run the same script by hand:

```bash
sudo /home/pi/dtk/scripts/provision-hostname.sh --name captua-2
sudo systemctl restart dtk
```
