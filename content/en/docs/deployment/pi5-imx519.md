---
title: "Raspberry Pi 5 IMX519 Camera Setup"
linkTitle: "Device Setup: Raspberry Pi 5 with IMX519 Camera"
url: /docs/deployment/pi5-imx519/
translationKey: docs-deployment-pi5-imx519
docs_section: deployment
source: docs/developers/device_setup_pi5_imx519.qmd
---

***

This guide explains how to connect and configure the **Arducam IMX519** camera on the **Raspberry Pi 5**, and how to test still captures using shell scripts.

## Tested Hardware {#tested-hardware}

* Raspberry Pi 5 – 8GB RAM
* Arducam IMX519 Camera Module, SKU: B0371 x 2
* CSI **22-to-22-pin Ribbon Cable** (15 cm or 20 cm recommended) x 2
* Raspberry Pi Official Power Supply (5V/3A or higher, 27 W PSU recommended)
* microSD Card 16 GB with Raspberry Pi OS (Legacy, 64-bit) Lite, Debian 12 "Bookworm", installed. Raspberry Pi Imager's plain "Raspberry Pi OS Lite (64-bit)" entry now installs Debian 13 "Trixie", which Captua has not been validated against.

Initial setup steps for Raspberry Pi OS can be found in the [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/computers/getting-started.html).

---

## 1. Hardware Connection {#hardware-connection}

For camera connection we followed the [Arducam Quick Start Guide for Hardware Setup](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/Quick-Start-Guide/#step-3-connect-to-raspberry-pi).

### Camera Connection {#camera-connection}

The actual camera connection looks like this:

{{< media id="imx519-ribbon-connection" >}}

Make sure the ribbon cable is fully and squarely seated in the connector before closing the retaining clip. Orientation on the Pi side is the same for both ports: the cable's **metal contacts face the Ethernet port**, with the blue stiffener toward the board's front edge (HDMI/USB-C side) — see the dual-camera photo below.

### Dual Camera Connection on Raspberry Pi 5 {#dual-camera-connection-on-raspberry-pi-5}

The Raspberry Pi 5 includes two CSI connectors labeled **CAM0** and **CAM1**. Connect one camera to each port using 22-pin ribbons.

> Both ports require the cable’s metal contacts to face the Ethernet port.

{{< media id="rpi5-camera-ribbon-connection" >}}

### Final Assembly {#final-assembly}

After connecting the cameras, ensure everything is securely in place. Attach any necessary heatsinks or cooling solutions, and insert the microSD card with Raspberry Pi OS installed. Finally, connect the power supply to boot up the Raspberry Pi 5. Attach peripherals (keyboard, mouse, monitor) or set up SSH for headless operation.

{{< media id="rpi5-imx519-b0371-setup" >}}

---

## 2. Software Setup {#software-setup}

For this step, we followed the [Arducam IMX519 Software Setup Guide](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/16MP-IMX519/), specifically the instructions for Raspberry Pi Bullseye OS 6.1.21 and Later / Bookworm OS.

> **Note on software stacks**: Raspberry Pi’s official `rpicam-apps` are generally preferred for Pi 5, but in our tests they did **not** successfully detect the IMX519. The method below, using Arducam’s packages, worked reliably. Other setups may succeed with `rpicam-apps`, but this guide documents the tested path.

**Step 1: Download the bash script**

```bash
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh

chmod +x install_pivariety_pkgs.sh
```

**Step 2: Install `libcamera`**

```bash
./install_pivariety_pkgs.sh -p libcamera_dev
```

**Step 3: Install libcamera-apps**

```bash
./install_pivariety_pkgs.sh -p libcamera_apps
```

**Step 4: Modify the boot configuration**

```bash
sudo nano /boot/firmware/config.txt
```

Add or modify the following:

```ini
# Disable auto-detect (doesn’t catch third-party sensors reliably)
camera_auto_detect=0

[all]
dtoverlay=imx519,cam0
dtoverlay=imx519
```

> The first line (`imx519,cam0`) explicitly enables CAM0. The second (`imx519`) allows the kernel to probe CAM1 automatically. Both are needed for dual-camera setups.

Optional: enable debug logging:

```ini
dtdebug=1
```

Save and reboot:

```bash
sudo reboot
```

---

## 3. Verify Camera Detection {#verify-camera-detection}

After rebooting:

```bash
rpicam-hello --list-cameras
```

Expected output (dual IMX519s):

```less
Available cameras
-----------------
0 : imx519 [4656x3496 …] (/base/axi/pcie@…/i2c@88000/imx519@1a)
1 : imx519 [4656x3496 …] (/base/axi/pcie@…/i2c@80000/imx519@1a)
```

If you want to confirm the media graph:

```bash
v4l2-ctl --list-devices
media-ctl -p
```

---

## 4. Test Cameras {#test-cameras}

**Preview from each camera**

```bash
rpicam-hello --camera 0 -t 5000
rpicam-hello --camera 1 -t 5000
```

**Capture a still image**

```bash
rpicam-jpeg --camera 0 -o cam0.jpg
rpicam-jpeg --camera 1 -o cam1.jpg
```

**Record short video**

```bash
rpicam-vid --camera 0 -t 10000 -o cam0.h264
rpicam-vid --camera 1 -t 10000 -o cam1.h264
```

---

## 5. Troubleshooting {#troubleshooting}

* **Error -5: failed to read chip id** → Sensor not responding on I²C

  * Reseat ribbon, check orientation.
  * Ensure latch is fully closed.
  * Try swapping CAM0 ↔ CAM1.

* **Only one camera detected** → Confirm both `dtoverlay` lines exist. Swap modules/cables to isolate the fault.

* **No `/dev/video0`** → Driver didn’t bind sensor. Check logs:

  ```bash
  dmesg | grep imx
  ```

* **Check power health** →

  ```bash
  vcgencmd get_throttled
  ```

  A value of `0x0` means the command has recorded none of the conditions it monitors. A non-zero value can indicate undervoltage, temperature limiting, or reduced clock frequency, either current or past. Check the result’s bits in the [Raspberry Pi documentation](https://www.raspberrypi.com/documentation/computers/os.html#get_throttled) to identify the cause. If it indicates undervoltage, use the official power supply.

* **Enable debug logs** (if `dtdebug=1` is set):

  ```bash
  dmesg | grep -i imx
  sudo vcdbg log msg
  ```

---
