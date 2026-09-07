# Hardware & Peripherals Guide
**Document ID:** KB-HW-006  
**Category:** Hardware / Devices  
**Last Updated:** 2024-01-15  
**Owner:** IT Desktop Support Team

---

## Overview

This guide covers the setup, configuration, and troubleshooting of hardware devices issued to or used by Acme Corp employees, including laptops, monitors, printers, USB peripherals, and docking stations.

All hardware faults or replacement requests must be logged as IT tickets. Do NOT attempt to open or physically repair corporate hardware yourself.

---

## Section 1 — Laptop Setup (New Device / Re-image)

### First Login (New Device)
1. Power on the device. It should boot into the Windows Out-of-Box Experience (OOBE).
2. If a setup wizard appears, connect to the `ACME-CORP` Wi-Fi during setup.
3. On the sign-in screen, click **Sign in with corporate account** (do NOT create a local account).
4. Enter your corporate email and AD password.
5. Complete MFA.
6. Intune will automatically enroll the device and push required software. This can take **20–45 minutes** on first login.
7. Do NOT interrupt the enrollment process. You may see the Company Portal and Windows Update running in the background.

### Corporate Laptop Standards
All Acme Corp employee laptops come pre-configured with:
- Windows 11 Enterprise (64-bit), fully patched
- Microsoft 365 Apps (Word, Excel, PowerPoint, Teams, Outlook)
- GlobalProtect VPN client
- Acme Corp Root CA certificate
- Microsoft Defender for Endpoint (antivirus + EDR)
- Bitlocker encryption (all corporate laptops are encrypted by default)

---

## Section 2 — Docking Station Setup

Acme Corp issues **Dell WD22TB4 Thunderbolt docking stations** to employees who use fixed workstations or work frequently in the office.

### Setup Steps
1. Connect the Thunderbolt 4 cable from the dock to your laptop's Thunderbolt/USB-C port.
2. Connect external monitors, keyboard, mouse, and Ethernet cable to the dock.
3. Connect the dock's power adapter.
4. Windows should automatically detect and install the dock drivers (connected to internet required).
5. If monitors do not appear, press `Win + P` and select **Extend**.

### Docking Station Not Detected / USB Devices Not Working
1. Unplug and replug the Thunderbolt cable.
2. Update the dock firmware:
   - Search Dell Thunderbolt Dock Firmware Update on Dell's support website.
   - Enter the dock's service tag (usually printed on the bottom of the dock).
3. Update Thunderbolt drivers via Device Manager → Firmware.
4. If still not working after firmware update, raise an IT hardware ticket.

---

## Section 3 — External Monitor Setup

### Connecting Monitors
1. Connect monitor via HDMI, DisplayPort, or through the docking station.
2. Right-click desktop → **Display Settings**.
3. Click **Detect** if the monitor is not shown.
4. Arrange the monitors by dragging them to the correct position relative to your laptop screen.
5. Set resolution: for Dell 24" monitors use **1920×1080**; for 27" 4K models use **3840×2160** at 60 Hz.

### Monitor Shows "No Signal"
1. Verify the cable is firmly connected at both ends.
2. Switch the monitor input source (HDMI 1, HDMI 2, DP) using the monitor's physical buttons.
3. Try a different cable — HDMI cables can fail.
4. Test with a different monitor or a different port on the dock.
5. Check Device Manager → Display Adapters for driver errors.

### Resolution / Blurry Text on External Monitor
1. Right-click desktop → Display Settings → select the external monitor → **Advanced display settings**.
2. Set recommended resolution (do not use a lower resolution as text will appear blurry).
3. In Display Settings → Scale → Set to **100%** for standard monitors or **150%** for 4K monitors.

---

## Section 4 — Printer Setup

### Finding Your Nearest Printer

Printers are deployed per floor and labeled on the floor map available on the intranet:
> `https://intranet.acmecorp.com/facilities/floorplans`

### Adding a Network Printer (Windows)

1. Open **Settings** → Printers & Scanners → **Add a printer or scanner**.
2. If the printer appears automatically, click Add.
3. If not found automatically:
   - Click **The printer that I want isn't listed**.
   - Select **Add a printer using an IP address or hostname**.
   - Enter the printer IP address (from the floor map or floor label).
4. Windows will download and install the printer driver from the network.

### Printer Driver via Deployment (Recommended)

IT pre-deploys printers to managed devices based on your floor assignment. If the correct printer is not in your printer list:
1. Check Company Portal → Devices → click on your device → **Sync** to force policy refresh.
2. Wait 10 minutes and check Printers & Scanners again.
3. If still missing, raise an IT ticket with your building, floor number, and printer label.

### Common Printer Issues

| Issue | Resolution |
|---|---|
| Print job stuck in queue | Open print queue (right-click printer in taskbar) → Cancel all documents |
| Printer offline | Turn printer off and back on; re-select "Use Printer Online" from print queue menu |
| Poor print quality | Replace toner cartridge via the floor's stationery cabinet or submit a supply request |
| "Access Denied" when printing | Confirm you have been added to the printer's security group — raise access ticket |
| Paper jam | Follow the paper jam clearing guide printed on the inside of the printer panel |

---

## Section 5 — USB Policy & Peripheral Policy

### USB Storage Devices

Per the **Acme Corp Data Security Policy**:
- **Personal USB drives are blocked** on corporate devices.
- Only IT-issued, **encrypted USB drives** (Apricorn Aegis) are permitted.
- Attempting to connect an unauthorized USB device triggers a **DLP (Data Loss Prevention) alert**.

To request an authorized USB drive: raise an IT ticket with your manager's approval and a business justification.

### USB Keyboards, Mice, Headsets

Standard USB keyboards, mice, and headsets are NOT restricted. Connect and use freely. Windows will auto-install drivers.

If a USB device is not recognized:
1. Try a different USB port (USB-A ports on the side vs. the dock).
2. Try the device on another laptop to confirm it is not faulty.
3. Check Device Manager for unknown device errors.

### Bluetooth Peripherals

Bluetooth peripherals are permitted. To connect:
1. Put the device in pairing mode.
2. Windows Settings → Bluetooth & devices → Add device.
3. Select the device and pair.

If Bluetooth is disabled (some security configurations disable it):
- Raise an IT ticket requesting a Bluetooth exception for your device if you have a valid business need.

---

## Section 6 — Hardware Faults & Replacement

### Reporting a Hardware Fault

Do NOT attempt to repair corporate hardware yourself. Raise an IT ticket with:
- Device name / serial number (found in Settings → System → About or on the laptop label)
- Description of the fault (display cracked, keyboard key missing, battery not charging, etc.)
- When the fault occurred
- Whether data access is blocked (prioritizes response)

### Hardware Replacement Process
- **Critical fault (cannot work):** Same-day loaner device arranged.
- **Non-critical fault (workaround available):** 2–5 business days for repair or replacement.
- Warranty claims for devices under 3 years old are handled by IT at no cost to the employee.

---

## Section 7 — Escalation

For hardware issues raise a ticket with:

- Device serial number (on the label on the bottom of the device)
- Issue description with photographs if helpful
- Whether the device was dropped, wet, or physically damaged (important for warranty)

**Ticket Priority:** High (if device is unusable) / Medium (if workaround exists)  
**Expected Response Time:** Same-day (High) / 2 business days (Medium)  
**Support Contact:** `it-helpdesk@acmecorp.com` or IT walk-in desk, Floor 3, Building A
