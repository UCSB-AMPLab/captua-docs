---
title: "Captua — Camera libraries"
linkTitle: "Camera libraries"
url: /docs/developers/camera-libraries/
translationKey: docs-developers-camera-libraries
docs_section: developers
---

Captua drives cameras through one of four backends. The `CAMERA_BACKEND` setting in `.env` chooses the backend. This page names the library behind each backend and the reference documentation for it. To run the native backend on a Raspberry Pi, see [Developer setup](/docs/developers/developer-setup/#option-2-raspberry-pi-mode-with-cameras).

## Choosing a backend {#choosing-a-backend}

| `CAMERA_BACKEND` | Cameras | Library | Code |
|---|---|---|---|
| `picamera2` (default) | Raspberry Pi camera modules, such as the IMX519 | picamera2, on libcamera | `backend/capture/backends/picamera2_backend.py` |
| `subprocess` | Raspberry Pi camera modules | the `rpicam-still` command from rpicam-apps, on libcamera | `backend/capture/backends/subprocess_backend.py` |
| `gphoto2` | DSLRs supported by libgphoto2, such as the Canon EOS Rebel T7 | python-gphoto2, on libgphoto2 | `backend/capture/backends/gphoto2_backend.py` |
| `chdk` | Canon compacts running the CHDK firmware add-on | pychdk, over pyusb | `backend/capture/backends/chdk_backend.py` |

The backend reads the value without surrounding spaces and without regard to case. If the value names none of these four, the backend refuses to start and names the valid values (`assert_camera_backend_configured` in `backend/capture/service.py`). It does not fall back to another backend, because a fallback would look like a dead camera.

Setting up the hardware for each backend is described in the camera guides: [Raspberry Pi 5 with IMX519 cameras](/docs/deployment/pi5-imx519/), [gPhoto2 cameras](/docs/cameras/gphoto2/) and [CHDK cameras](/docs/cameras/chdk/).

## picamera2 and rpicam-apps (libcamera) {#libcamera}

The `picamera2` and `subprocess` backends both reach the Raspberry Pi camera modules through libcamera. `picamera2` uses the picamera2 Python library directly, with streaming, live preview and settings that change while the camera runs. `subprocess` runs the `rpicam-still` command for each capture.

picamera2 and libcamera come from the Raspberry Pi OS packages `python3-picamera2` and `python3-libcamera`, not from pixi. `scripts/setup.sh` installs them, and `pixi run setup-camera-link` puts them on the pixi environment's path. numpy stays below 2 in `backend/pixi.toml` and `backend/requirements.txt`, because numpy 2 breaks the system-built picamera2 dependencies.

- [Raspberry Pi camera software](https://www.raspberrypi.com/documentation/computers/camera_software.html): the rpicam-apps commands, libcamera and picamera2

## gPhoto2 {#gphoto2}

The `gphoto2` backend uses [python-gphoto2](https://github.com/jim-easterbrook/python-gphoto2), the Python binding to libgphoto2 (`gphoto2>=2.6.3,<3` in `backend/pixi.toml`). On a unit, `scripts/setup.sh` installs the `gphoto2` command and builds python-gphoto2 from source against the system libgphoto2 (`gphoto2==2.6.4`). The binary wheel from PyPI bundles its own libgphoto2 and libusb, and on Raspberry Pi OS Bookworm its autodetection finds no cameras even when the system's `gphoto2` command lists them.

- [libgphoto2 API documentation](http://www.gphoto.org/doc/api/index.html): the most complete description of the library
- [gphoto2 command reference](http://www.gphoto.org/doc/manual/ref-gphoto2-cli.html): the command-line tool, useful for checking a camera by hand
- [python-gphoto2](https://github.com/jim-easterbrook/python-gphoto2): the binding Captua uses

## CHDK {#chdk}

The `chdk` backend talks to Canon compacts running CHDK over PTP and USB through pychdk, a library maintained in the UCSB-AMPLab organisation and pinned to a tag (`v0.1.3` in `backend/pixi.toml`). pychdk uses pyusb (`pyusb>=1.2,<2`), with no Lua or C on the host. `scripts/provision-chdk-usb.sh` installs libusb, a udev rule and the group membership that let the backend open the cameras. Both `scripts/setup.sh` and `scripts/update.sh` run it.

- [pychdk](https://github.com/UCSB-AMPLab/pychdk): the library and its documentation
