# VPN Troubleshooting Guide
**Document ID:** KB-VPN-001  
**Category:** Network / Remote Access  
**Last Updated:** 2024-01-15  
**Owner:** IT Infrastructure Team

---

## Overview

Acme Corp uses **GlobalProtect VPN** (Palo Alto Networks) to provide secure remote access to internal systems, shared drives, and corporate applications. All employees working remotely are required to connect through the corporate VPN before accessing internal resources.

This document covers the most common VPN issues, their causes, and step-by-step resolution procedures.

---

## Section 1 — VPN Client Installation

### Supported Platforms
- Windows 10 / 11 (64-bit)
- macOS 12 Monterey and above
- Ubuntu 20.04 LTS and above

### Download Location
The GlobalProtect VPN client is available via the internal software portal:
> **https://software.internal.acmecorp.com/vpn**

You must be on the **corporate Wi-Fi network (ACME-CORP)** or have a temporary access token from IT to download the installer.

### Installation Steps (Windows)
1. Download `GlobalProtect-win64.msi` from the software portal.
2. Run the installer as Administrator (right-click → Run as administrator).
3. Follow the on-screen setup wizard. Accept all defaults.
4. When prompted for the **Portal Address**, enter: `vpn.acmecorp.com`
5. Click Connect. Log in with your **corporate email** and **Active Directory (AD) password**.
6. Complete the **MFA challenge** using the Acme Authenticator app.

---

## Section 2 — Common VPN Errors and Fixes

### Error 809 — VPN Connection Timeout (Most Common)

**What it means:** The VPN client cannot establish a connection to the VPN gateway, usually due to a firewall or network block.

**Causes:**
- You are on a network that blocks UDP port 4500 (hotels, airports, some home ISPs).
- The VPN gateway is temporarily unavailable.
- Your local firewall is blocking the VPN client.

**Resolution Steps:**
1. Check your internet connection first. Open a browser and confirm you can reach `https://www.google.com`.
2. If on a hotel/airport network, request access code from the front desk or switch to mobile hotspot.
3. Change the VPN connection protocol:
   - Open GlobalProtect → Settings → General
   - Change **Preferred Tunnel** from `IPSec` to `SSL`
   - Click Save and reconnect.
4. Temporarily disable Windows Firewall and retry. If it connects, add a firewall exception for `GlobalProtect.exe`.
5. Restart the GlobalProtect service:
   - Press `Win + R` → type `services.msc`
   - Find **PAN GlobalProtect** → Right-click → Restart
6. If still failing, contact IT support. Mention: Error 809, your ISP name, and whether you tried SSL mode.

---

### Error 10013 — Access Denied by Local Firewall

**What it means:** A local security policy or third-party antivirus is blocking the VPN.

**Resolution Steps:**
1. Open Windows Defender Firewall → Allow an App through Firewall.
2. Click **Change Settings** → **Allow another app**.
3. Browse to `C:\Program Files\Palo Alto Networks\GlobalProtect\GlobalProtect.exe`.
4. Add both Public and Private network access.
5. Retry VPN connection.

---

### Error — Invalid Portal Address

**What it means:** The portal address configured is incorrect.

**Correct portal address:** `vpn.acmecorp.com`

**Resolution Steps:**
1. Open GlobalProtect client.
2. Click the gear icon → Settings.
3. Under Portal, confirm the address is exactly: `vpn.acmecorp.com`
4. If incorrect, clear the field and retype it. Click Save. Reconnect.

---

### Error — Certificate Warning / Untrusted Certificate

**What it means:** Your device doesn't trust the corporate certificate authority (CA).

**Resolution Steps:**
1. Download the Acme Corp Root CA certificate from:
   > https://it.internal.acmecorp.com/certificates/AcmeCorpRootCA.crt
2. Double-click the `.crt` file → Install Certificate.
3. Select **Local Machine** → Place in **Trusted Root Certification Authorities**.
4. Restart GlobalProtect and reconnect.

---

### VPN Connects but Cannot Reach Internal Resources

**Symptoms:** VPN shows Connected status but internal sites (SharePoint, JIRA, internal apps) are unreachable.

**Causes:**
- Split-tunnel routing issue.
- DNS not resolving internal hostnames.

**Resolution Steps:**
1. Open Command Prompt and run:
   ```
   nslookup jira.internal.acmecorp.com
   ```
   If it returns an IP, DNS is working. If it fails, proceed to step 2.
2. Check VPN DNS settings:
   - Open Network Connections (Control Panel)
   - Find the GlobalProtect adapter → Properties → TCP/IPv4
   - Set DNS to: `10.0.0.10` (Primary), `10.0.0.11` (Secondary)
3. Flush DNS cache:
   ```
   ipconfig /flushdns
   ```
4. Ping the internal gateway:
   ```
   ping 10.0.0.1
   ```
   If ping fails, escalate to IT Infrastructure.

---

### VPN Disconnects Frequently

**Causes:**
- Unstable internet connection.
- Power-save settings suspending the network adapter.

**Resolution Steps:**
1. Disable network adapter power saving:
   - Device Manager → Network Adapters → Your adapter → Properties → Power Management
   - Uncheck "Allow the computer to turn off this device to save power"
2. Change DNS to `8.8.8.8` temporarily and retry.
3. Use a wired (Ethernet) connection instead of Wi-Fi if available.

---

## Section 3 — MFA / Authentication Issues

### Cannot Complete MFA Challenge

**Resolution Steps:**
1. Ensure your mobile device has the **Acme Authenticator** app installed.
2. Confirm your device time is synchronized (wrong system time breaks TOTP codes).
3. If you have lost access to your authenticator, contact IT immediately:
   - Email: `it-helpdesk@acmecorp.com`
   - Phone: `+1-800-IT-ACME (ext. 1001)`
   - An IT engineer will reset your MFA enrollment within 2 business hours.

### Account Locked After VPN Login Failures

If you enter your password incorrectly 5 times, your Active Directory account will be locked for **30 minutes** automatically.

To unlock immediately: Contact IT Helpdesk with your Employee ID.

---

## Section 4 — VPN Gateway Status

Before troubleshooting client-side issues, check the VPN gateway status:
> **https://status.acmecorp.com**

If the VPN service shows **Degraded** or **Outage**, wait for IT to restore the service before attempting reconnection.

---

## Section 5 — Escalation

If none of the above steps resolve your issue, create an IT support ticket with the following information:

- Your Employee ID
- Operating system and version
- GlobalProtect version (Help → About)
- Exact error code / message
- Network type (home Wi-Fi, hotel, mobile hotspot, corporate office)
- Steps you have already tried

**Ticket Priority:** Medium  
**Expected Response Time:** 4 business hours  
**Escalation Contact:** IT Infrastructure Team (`infra@acmecorp.com`)
