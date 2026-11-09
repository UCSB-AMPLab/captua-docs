---
title: "External Storage"
url: /docs/operators/external-storage/
translationKey: docs-operators-external-storage
docs_section: operators
source: docs/users/external-storage.qmd
---

Captua can save captured images to an external USB drive or SD card instead of
the unit's internal storage. This is useful when digitizing large collections that would exceed
the capacity of the built-in microSD card.

{{< callout type="warning" title="Experimental feature" >}}
This feature depends on operating-system-level disk operations. Compatibility varies by drive
format and hardware. See [Supported formats](#supported-formats) below. Do not rely on an
external drive as your **only** copy of digitized material — always keep a backup.
{{< /callout >}}

---

## How it works {#how-it-works}

While an external drive is **active**, Captua saves every new capture to a `dtk-projects/` folder
on that drive. This includes new captures for volumes you started on the internal card, so the
images of such a volume end up on two disks. Images captured earlier stay where they are and
remain readable. To keep each volume on one disk, activate the drive or restore internal storage
between volumes, not while a volume is in progress. Only one external location can be active at a
time.

If the active drive is disconnected or not mounted, Captua does not switch to the internal card.
It refuses to save new captures until an administrator connects and activates the drive again, or
restores internal storage.

---

## Preparing the drive {#supported-formats}

### Recommended format: exFAT {#recommended-format-exfat}

**exFAT** is the recommended format for external drives used with Captua. It is:

- Compatible with Linux, Windows, and macOS (no drivers needed on any platform)
- Supports files larger than 4 GB (important for high-resolution image sets)
- Well-supported on Raspberry Pi OS

### How to format a drive as exFAT {#how-to-format-a-drive-as-exfat}


#### Linux / Raspberry Pi {#linux-raspberry-pi}

```bash
# Install the exFAT tools if not already present
sudo apt install exfatprogs

# Identify the drive (look for your USB device — e.g. /dev/sda2)
lsblk

# Format the partition (replace /dev/sdXN with your actual partition)
sudo mkfs.exfat /dev/sdXN
```

{{< callout type="caution" >}}
Double-check the device path with `lsblk` before running `mkfs`. Formatting the wrong partition
will permanently erase its contents.
{{< /callout >}}

#### Windows {#windows}

1. Open **File Explorer** and right-click the drive → **Format…**
2. Set **File system** to `exFAT`
3. Click **Start**

#### macOS {#macos}

1. Open **Disk Utility** (Applications → Utilities → Disk Utility)
2. Select the drive in the left panel
3. Click **Erase**, set **Format** to `ExFAT`, then click **Erase**


### Format compatibility summary {#format-compatibility-summary}

| Format | Works with Captua | Notes |
|--------|:--------------:|-------|
| **exFAT** | ✅ Recommended | Best cross-platform choice |
| **ext4** | ✅ Supported | Linux-only; slightly faster |
| **FAT32 (vfat)** | ✅ Supported | 4 GB file size limit |
| NTFS | ⚠️ May work | Requires `ntfs-3g`; not guaranteed |
| APFS | ❌ Not supported | macOS-only filesystem |
| HFS+ | ❌ Not supported | macOS-only filesystem |

---

## Using external storage in the UI {#using-external-storage-in-the-ui}

{{< callout type="note" >}}
Only an administrator can do this. **Settings** does not appear in the sidebar for operators and reviewers.
{{< /callout >}}

Go to **Settings** (the gear icon in the sidebar). In the **Storage** section, click
**Storage drive** (marked experimental) to expand it.

### Step 1 — Connect the drive {#step-1-connect-the-drive}

Plug the USB drive or SD card into the Raspberry Pi. The drive does not need to be
mounted beforehand.

### Step 2 — Mount the drive {#step-2-mount-the-drive}

The device list shows the partitions Captua can use. Unmounted partitions have a **Mount**
button.

1. Find the partition you want to use in the list
2. Click **Mount**
3. Captua mounts the drive, and the row then shows **Activate** and **Unmount**

### Step 3 — Activate the drive {#step-3-activate-the-drive}

Click **Activate** next to the mounted partition. Captua:

1. Creates a `dtk-projects/` directory on the drive (if it does not exist)
2. Sets that directory as the active projects location
3. Shows a green **active** badge on the device row, **✓ In use** in place of the **Activate** button, and a banner confirming the active path

From this point, every new capture is stored on the external drive.

### Deactivating / reverting to internal storage {#deactivating-reverting-to-internal-storage}

Click **Restore default** in the banner to switch back to the
internal storage. The external drive is **not** unmounted — existing projects on it remain
intact and accessible.

### Safely removing the drive {#safely-removing-the-drive}

Before physically unplugging the drive:

1. If it is the active storage location, you can click **Restore default** first. Clicking **Unmount** on the active drive also switches back to internal storage.
2. Click **Unmount** next to the partition
3. Wait for the success message
4. Unplug the drive

Captua can unmount only drives it mounted itself with **Mount**.

{{< callout type="important" >}}
Always click **Unmount** before unplugging. Removing a drive while it is mounted can
corrupt the filesystem and cause data loss.
{{< /callout >}}

---

## Troubleshooting {#troubleshooting}

**Drive not appearing in the list**
: Captua lists the partitions it can use. It leaves out the operating system's own partitions and
partitions whose filesystem it cannot use, such as APFS and HFS+. A drive formatted without a
partition table does not appear either: create a partition on it with Disk Utility or another
partitioning tool, then format that partition (for example `/dev/sdX1`) as exFAT. If the drive uses
APFS or HFS+, reformat it as exFAT as well. Then click **Refresh list**. If the drive still does not
appear, check that it is properly connected and recognised by the OS (`lsblk` in a terminal).

**"Mount" returns an error**
: The filesystem may have errors, or the drive may need additional kernel modules (NTFS).
Reformat the drive as exFAT and try again.

**"Activate" fails with a permission error**
: This can happen on freshly formatted ext4 drives where the filesystem root is owned by
`root`. Captua attempts a fallback using elevated privileges. If it still fails,
reformat the drive as exFAT.

**Drive mounted but read-only**
: Some drives enforce read-only mode when almost full or when the filesystem has errors.
Check available space and run `sudo fsck /dev/sdXN` (with the drive unmounted) to repair
any filesystem errors.
