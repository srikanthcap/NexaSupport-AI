# Network & Wi-Fi Troubleshooting Guide
**Document ID:** KB-NET-005  
**Category:** Network / Connectivity  
**Last Updated:** 2024-01-15  
**Owner:** IT Infrastructure Team

---

## Overview

Acme Corp operates a managed enterprise network across all office locations. The corporate wireless network uses **WPA2-Enterprise (802.1X)** authentication, meaning your corporate credentials (email + password) are used to connect — there is no shared Wi-Fi password.

Network drives and internal application access require connection to either the **corporate office network** or the **GlobalProtect VPN** (for remote workers).

---

## Section 1 — Corporate Wi-Fi Networks

| SSID | Purpose | Authentication |
|---|---|---|
| `ACME-CORP` | Primary corporate network | 802.1X (corporate credentials) |
| `ACME-GUEST` | Guest and contractor network | Captive portal (lobby reception issues a code) |
| `ACME-IOT` | IoT devices and printers | Managed by IT (not for laptops) |

**Important:** Do NOT connect personal devices to `ACME-CORP`. Personal devices may only use `ACME-GUEST`. Connecting personal devices to `ACME-CORP` violates security policy.

---

## Section 2 — Connecting to ACME-CORP Wi-Fi

### Windows 10/11
1. Click the Wi-Fi icon in the taskbar → Select `ACME-CORP`.
2. Connection type will automatically use **WPA2-Enterprise**.
3. When prompted, enter:
   - Username: your corporate email (`firstname.lastname@acmecorp.com`)
   - Password: your Active Directory password
4. If prompted for a certificate, click **Connect** — the Acme Corp internal CA certificate is pre-installed on managed devices.
5. Connection should complete within 10–15 seconds.

### macOS
1. Click Wi-Fi icon → Select `ACME-CORP`.
2. Enter your corporate email and AD password.
3. You may be asked to trust the server certificate. Click **Trust** — verify the certificate shows `acmecorp.com` before trusting.

### If Your Device Is Not Managed (No Pre-Installed Certificate)
Contact IT helpdesk to install the Acme Corp Root CA certificate before connecting. Connecting without the correct certificate will fail at the authentication step.

---

## Section 3 — Common Wi-Fi Issues

### "Cannot Connect to ACME-CORP" / Authentication Failed

**Causes:**
- Incorrect credentials (password recently changed but not updated).
- Account locked.
- Certificate mismatch.

**Resolution Steps:**
1. Verify your AD password is correct by logging into `https://mail.acmecorp.com`.
2. If your password was recently changed, forget the `ACME-CORP` network and reconnect with the new password:
   - Windows: Settings → Network → Wi-Fi → Manage known networks → ACME-CORP → Forget
   - Reconnect and enter new credentials.
3. Confirm your account is not locked (see KB-AUTH-003).
4. Ensure the Acme Corp Root CA certificate is installed on your device.

### Connected to ACME-CORP but No Internet or Intranet Access

**Resolution Steps:**
1. Confirm IP address is in the corporate range:
   - Open Command Prompt → run `ipconfig`
   - IP should start with `10.x.x.x` or `192.168.x.x`
   - If it shows `169.254.x.x`, there is a DHCP problem — continue to step 2.
2. Release and renew IP:
   ```
   ipconfig /release
   ipconfig /renew
   ```
3. Flush DNS cache:
   ```
   ipconfig /flushdns
   ```
4. Ping the default gateway (shown in ipconfig output). If ping fails, the connection is at Layer 2/3 — contact IT Infrastructure.
5. Try pinging an internal resource: `ping jira.internal.acmecorp.com`
6. If internal ping works but internet doesn't, proxy settings may be blocking external traffic — see Section 5.

### Wi-Fi Drops Frequently / Unstable Connection

**Resolution Steps:**
1. Check for interference — move closer to the access point or a different room.
2. Update Wi-Fi adapter drivers:
   - Device Manager → Network Adapters → Wi-Fi adapter → Right-click → Update driver → Search automatically.
3. Disable Wi-Fi power saving:
   - Device Manager → Network Adapters → Wi-Fi adapter → Properties → Power Management
   - Uncheck "Allow the computer to turn off this device to save power."
4. Switch to 5 GHz band if your adapter supports it (provides less range but more stable connection near access points).
5. Report persistent drops to IT with your location (floor, room number, building) — may indicate an access point issue.

---

## Section 4 — Network Drive Mapping (Shared Drives)

Corporate network drives are accessible from `\\fileserver.internal.acmecorp.com\`.

| Drive Letter | Path | Purpose |
|---|---|---|
| F: | `\\fileserver.internal.acmecorp.com\shared` | Company-wide shared files |
| G: | `\\fileserver.internal.acmecorp.com\dept\<your_dept>` | Department files |
| H: | `\\fileserver.internal.acmecorp.com\home\<username>` | Your personal network home directory |

### Mapping a Network Drive (Windows)
1. Open **File Explorer** → Right-click **This PC** → **Map network drive**.
2. Choose a drive letter (e.g., `F:`).
3. Enter the path: `\\fileserver.internal.acmecorp.com\shared`
4. Check **Reconnect at sign-in**.
5. Check **Connect using different credentials** (enter your corporate email and password).
6. Click **Finish**.

### "Network Path Not Found" Error When Mapping Drive
1. Verify you are on corporate network or VPN.
2. Test connectivity: `ping fileserver.internal.acmecorp.com`
3. Check your access: not all departments can access all shares. Confirm with your manager that you have been added to the correct security group.
4. If you need access to a specific share, raise an IT Access Request ticket.

---

## Section 5 — Proxy Settings

Acme Corp uses a web proxy (`proxy.acmecorp.com:8080`) for internet traffic filtering on the office network.

Corporate-managed devices are pre-configured with the correct proxy settings. If you have recently re-imaged your device or changed browsers, you may need to configure it manually.

### Manual Proxy Configuration (if needed)
- Proxy address: `proxy.acmecorp.com`
- Port: `8080`
- Exceptions (no proxy for internal sites): `*.acmecorp.com;*.internal.acmecorp.com;localhost;127.0.0.1;10.*`

**Note:** Proxy settings are bypassed when connected to VPN (VPN routes internal traffic directly).

### "Access Denied" on a Website While on Corporate Network

1. Certain websites are blocked by the IT web filter (gaming, social media, streaming, etc.) per the Acceptable Use Policy.
2. If you believe a business site is incorrectly blocked, raise a **Web Filter Exception Request** ticket with the URL and business justification.

---

## Section 6 — Escalation

For unresolved network issues, raise a ticket with:

- Device name and OS version
- SSID you are trying to connect to
- Your physical location (building, floor, room)
- Output of `ipconfig /all` (copy-paste or screenshot)
- Output of `ping 8.8.8.8` (to test external connectivity)

**Ticket Priority:** High (network access blocks all work)  
**Expected Response Time:** 2 business hours  
**Network Team Contact:** `network-team@acmecorp.com`
