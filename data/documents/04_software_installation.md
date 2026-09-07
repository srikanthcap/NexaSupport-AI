# Software Installation Guide
**Document ID:** KB-SW-004  
**Category:** Software / Applications  
**Last Updated:** 2024-01-15  
**Owner:** IT Desktop Support Team

---

## Overview

Acme Corp manages software through a centralized deployment platform using **Microsoft Intune** (for modern managed devices) and **SCCM/MECM** (for legacy managed devices). All corporate-managed devices (laptops, desktops) receive software via the **Company Portal** app.

**Important:** Employees are NOT permitted to install unapproved software on corporate devices. Unauthorized software installation violates the Acceptable Use Policy and may trigger a security alert.

---

## Section 1 — Approved Software List

The following applications are approved for installation by employees from the Company Portal:

| Category | Application | Version |
|---|---|---|
| Office Suite | Microsoft 365 Apps | Latest |
| Browser | Google Chrome, Mozilla Firefox, Microsoft Edge | Latest |
| Communication | Microsoft Teams, Zoom | Latest |
| Code Editor | Visual Studio Code | Latest |
| Python | Python 3.11+ | 3.11 |
| Git | Git for Windows | Latest |
| PDF Reader | Adobe Acrobat Reader | Latest |
| Password Manager | LastPass (Enterprise) | Latest |
| Virtual Machine | VMware Workstation Player | 17.x |
| Database Client | DBeaver Community | Latest |
| SSH Client | PuTTY, OpenSSH (Windows built-in) | Latest |

---

## Section 2 — Installing Software via Company Portal

### Steps (Windows)
1. Click **Start** → search for **Company Portal**.
2. If Company Portal is not installed, download it from the Microsoft Store.
3. Sign in with your corporate Microsoft 365 credentials.
4. Browse or search for the application you need.
5. Click **Install**. The installation happens in the background (no admin rights needed).
6. You will receive a notification when the installation is complete.
7. Some applications require a device restart. Save all work before restarting.

### Why No Admin Password Is Needed
Intune deploys software with elevated privileges at the system level. You do not need local administrator rights because the installation is authorized and managed centrally by IT.

---

## Section 3 — Installing Python (For Data Science / Engineering Team)

Python is available via the Company Portal. However, for teams that require specific versions or virtual environments:

1. Install Python from Company Portal (Python 3.11 is the approved version).
2. To verify: open Command Prompt and run:
   ```
   python --version
   ```
   Expected output: `Python 3.11.x`

3. Install `pip` packages using a virtual environment — do NOT install packages globally:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install <package_name>
   ```

4. If you need a package not available via pip (e.g., a compiled binary), raise an IT ticket for review before installation.

---

## Section 4 — Requesting Software Not in the Approved List

If you need software that is not available in the Company Portal:

1. Raise an **IT Software Request ticket** with:
   - Software name and version
   - Official download URL
   - Business justification (why you need it)
   - Manager approval
2. IT Security will review the request within **3–5 business days**.
3. If approved, IT will test, package, and deploy the software via Intune/SCCM.
4. If rejected, IT will suggest an approved alternative.

**Do NOT download and install software from external websites yourself.** This is a security violation and may result in disciplinary action.

---

## Section 5 — Common Installation Issues

### "Company Portal is not available" / Cannot sign in to Company Portal

**Resolution Steps:**
1. Ensure you are connected to corporate network or VPN.
2. Confirm your Microsoft 365 license is active: go to `https://myaccount.microsoft.com` and check Subscriptions.
3. If Company Portal is missing from Start menu, open Microsoft Store → search Company Portal → Install.
4. If license issue is suspected, raise an IT ticket with your Employee ID.

### Installation Stuck / Frozen in Company Portal

**Resolution Steps:**
1. Wait 15 minutes — large apps (e.g., Microsoft 365) can take time on slow connections.
2. Check network speed: `https://speedtest.acmecorp.com`
3. If still stuck: open Task Manager → Services → `IntuneManagementExtension` → Restart.
4. Retry the installation from Company Portal.

### "Access Denied" or "Insufficient Permissions" During Installation

This happens when someone tries to install software outside the Company Portal (e.g., directly from a downloaded `.exe`).

**Resolution Steps:**
1. Do NOT try to install using the downloaded installer directly.
2. Request the software through Company Portal or raise a ticket if it is not listed.
3. If you have a legitimate need for local admin rights temporarily (e.g., for development), raise an **Elevated Access Request** ticket. Temporary admin access is granted for specific tasks with time limits.

### Microsoft 365 Apps "Your subscription has expired"

**Resolution Steps:**
1. Open any Office app (Word, Excel) → File → Account → **Activate Product**.
2. Sign in with your corporate email (`firstname.lastname@acmecorp.com`).
3. If the license still shows expired, sign out and back in:
   - Start → Settings → Accounts → Access work or school → Disconnect → Reconnect
4. If unresolved, raise an IT ticket — the M365 license may need reassignment.

---

## Section 6 — Software License Management

- All software licenses are managed centrally by the IT Procurement team.
- Employees cannot purchase software licenses on behalf of the company independently.
- If you have a business need for a licensed application, submit a **Software License Request** to `it-procurement@acmecorp.com` with manager approval.
- Reassigning licenses from departing employees to new hires requires an IT ticket.

---

## Section 7 — Escalation

For unresolved software issues, raise a ticket with:

- Device name (found in Settings → System → About → Device name)
- Operating system version
- Software name and version requested/installed
- Exact error message
- Screenshot if available

**Ticket Priority:** Medium  
**Expected Response Time:** 4 business hours  
**Support Contact:** `it-helpdesk@acmecorp.com`
