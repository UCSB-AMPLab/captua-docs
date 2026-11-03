---
title: "Setting Up gPhoto2-Compatible Cameras"
url: /docs/cameras/gphoto2/
translationKey: docs-cameras-gphoto2
docs_section: cameras
source: docs/users/setting-up-gphoto2-cams.qmd
---

{{< callout type="note" title="List of gPhoto2 compatible cameras" appearance="simple" collapse="true" >}}

For a comprehensive list of gPhoto2-supported cameras, visit the [official support page](http://gphoto.org/proj/libgphoto2/support.php).

To be fully compatible with the Digitization Toolkit software, cameras should support all of the following capabilities: Image Capture, Trigger Capture, Live View, and Configuration.
{{< /callout >}}

## Connect the cameras to the Raspberry Pi {#connect-the-cameras-to-the-raspberry-pi}

- **Requirements**:
    - 2 x USB 2.0 Type-A to Mini-B (5-pin) **data** cables

{{< callout type="warning" appearance="simple" >}}
Many mini-B cables sold today are **charge-only** and carry no data lines. A charge-only cable produces no symptom on the camera and nothing on the Pi — the camera simply never appears. Two brand-new cables failed exactly this way during hardware validation (one intermittent `error -71` in `dmesg`, then electrical silence). Use cables known to carry data, seat both ends firmly, and verify with `lsusb` (below) before suspecting anything else.
{{< /callout >}}

- **Connections**:
    - Camera side: Plug into the middle port (marked with the USB trident icon).
    - Raspberry Pi side: Plug into any USB-A port (preferably a blue USB 3.0 port).

{{< media id="cannon-eos-rebelt7-usb4cam" >}}

{{< media id="cannon-eos-rebelt7-usb2rpi" >}}

## Verify the connection {#verify-the-connection}

With both cameras connected and **switched on**, run on the Pi:

```bash
lsusb                  # expect one "Canon, Inc." line per camera body
gphoto2 --auto-detect  # expect both cameras listed
```

If a camera is missing: reseat both cable ends, power-cycle the camera body, and check `dmesg | tail` — repeated `error -71` messages point to a bad cable or a poorly seated plug; total silence with a powered-on camera points to a charge-only cable.

## Canon EOS Rebel T7 {#canon-eos-rebel-t7}

- Set the focus mode to "Manual Focus": On the lens switch, set the focus mode to MF (Manual Focus).

{{< media id="cannon-eos-rebelt7-lensmf" >}}

- Set the mode to Manual: rotate the mode dial to M (Manual).

{{< media id="cannon-eos-rebelt7-mode" >}}

- Retract the built-in flash: If the flash pops up after turning on the camera, push the flash head down into the closed position.

{{< media id="cannon-eos-rebelt7-flash" >}}

- Set Auto power off: From the camera menu, find the Auto power off setting and set it to 15 minutes.

{{< media id="cannon-eos-rebelt7-config-menu" >}}

{{< callout type="caution" appearance="simple" >}}
When the software opens a session on a body, which happens on the first preview, capture, or settings read after the body is switched on, it attempts to switch the body's Auto power off setting off so the camera cannot sleep mid-session; it never powers the camera off itself. Until a session has been opened, the body's own setting applies, so a body that sat idle before the first preview of the day may already have left the USB bus. If the Raspberry Pi crashes or is powered off while a session is open, the camera can stay on until you switch it off by hand.
{{< /callout >}}

{{< callout type="important" appearance="simple" >}}
When Auto power off fires, the camera does not just sleep — it **drops off the USB bus entirely** (`lsusb` no longer lists it), and the software cannot wake it: a slept body looks exactly like a disconnected one, and the interface will show the camera as not connected. To bring it back, **half-press the shutter button** on the camera, wait a few seconds for it to re-enumerate, then press **Reconnect cameras** in the interface (on the dashboard camera panel or in the live preview controls). The same action recovers a body whose USB cable was reseated. Keep this in mind before unplugging anything or restarting services.
{{< /callout >}}
