---
title: "Captua — Operator card"
linkTitle: "Operator card"
url: /docs/operators/card/
translationKey: docs-operators-card
docs_section: operators
toc: false
---

A one-page guide for the people who operate the scanner. Print it and keep it next to the scanner.

## Shutting down and restarting the scanner {#shutting-down-and-restarting-the-scanner}

1. If a capture is in progress, wait for it to finish.
2. Open the user menu. In **Overview** and **Projects**, click your user name at the bottom of the sidebar; if the sidebar is collapsed, click the box with the first two letters of your name. On the capture screen and the volume screen, click the circle with those letters at the top right.
3. Click "Shut down the scanner", then "Yes, shut down" to confirm.
4. "Shutting down the scanner…" appears. Unplug the power only when the screen goes dark.

To restart, click "Restart the scanner" in the same menu, then "Yes, restart". The screen goes dark for a moment. Don't unplug the power until the application appears again.

If you are an administrator, you also have "Shut down" and "Restart" buttons in **Settings → Power**.

**If the screen doesn't respond:** press the scanner's power button once. This shuts the scanner down safely. Wait for the screen to go dark before you unplug the power.

**If the scanner stays on:** press **Ctrl+Alt+F2**, type `sudo poweroff`, and press Enter. Wait for the screen to go dark.

{{< callout type="warning" appearance="simple" >}}
**Never unplug the power while the scanner is on:** you can damage the memory card and lose data.
{{< /callout >}}

## Switching screens {#switching-screens}

- **Ctrl+Alt+F2** → text screen (recovery)
- **Ctrl+Alt+F1** → the application

Use the left Ctrl and Alt keys; the right ones don't work for these shortcuts.

## Canon DSLR cameras: focusing at the start of the day {#canon-dslr-cameras-focusing-at-the-start-of-the-day}

1. Set the lens switch to **AF** on both cameras and take the first capture. Both cameras focus on their own.
2. Move the switch to **MF**, also **on both cameras**. Focus then holds for the rest of the day, because the distance between camera and document doesn't change.

If you leave the switch on AF, each capture takes about 12 seconds longer and can hang. If that happens, the capture screen may show a warning in the "Camera Controls" panel. Before you start digitizing, look at each camera's lens and check that the switch is on **MF**. Captua tries to turn the flash off. Check that the flash is closed before you start.

## Sending a finished volume for review {#sending-a-finished-volume-for-review}

1. Open the volume: **Projects →** your project **→** the volume.
2. Click "Send for review" in the top bar. If you already sent part of the volume, the button shows how many new records you are about to send (for example, "Send 3 new records").
3. Click "Send" to confirm.

From then on the records are under review and you can't move them to another volume. If you made a mistake, click "Withdraw from review", then "Withdraw" to confirm. This withdraws only the records not yet reviewed; approved and rejected records stay as they are.

## If the cameras don't appear {#if-the-cameras-dont-appear}

1. If a camera has switched itself off, half-press the shutter button to wake it, or plug its USB cable in again.
2. Click "Reconnect cameras". It's in **Overview**, under "Test cameras", and on the capture screen, in the "Camera Controls" panel (open it with the gear icon).
3. If they still don't appear, click "Log out" in the user menu (see above) and log in again.

## If a camera stops responding {#if-a-camera-stops-responding}

1. On Canon DSLRs, check that the lens switch is on **MF** (see above).
2. Switch that camera off and on again, then click "Reconnect cameras".
3. If nothing changes, restart the scanner from the user menu (see above).

## If the application freezes {#if-the-application-freezes}

Press **Ctrl+Alt+F2**, type `sudo systemctl restart dtk`, and press Enter. **No message appears after you press Enter; this is normal.** Wait about 30 seconds, then go back to the application with **Ctrl+Alt+F1**.

If the application still doesn't respond, shut the scanner down with the power button (see above) and switch it on again.
