# Email & Outlook Troubleshooting Guide
**Document ID:** KB-EMAIL-002  
**Category:** Communication / Email  
**Last Updated:** 2024-01-15  
**Owner:** IT Desktop Support Team

---

## Overview

Acme Corp uses **Microsoft 365 (Office 365)** for corporate email, calendar, and collaboration. The primary email client is **Microsoft Outlook** (desktop and mobile). Web access is available at `https://mail.acmecorp.com` (redirects to Outlook Web Access / OWA).

This document covers common email configuration problems, Outlook errors, calendar issues, and mobile mail setup.

---

## Section 1 — Initial Email Account Setup

### What You Need
- Corporate email address (format: `firstname.lastname@acmecorp.com`)
- Active Directory password
- MFA-enrolled device

### Outlook Auto-Configuration (Recommended)
1. Open Outlook → File → Add Account.
2. Enter your corporate email address.
3. Click **Connect**. Outlook will auto-discover the server settings via Microsoft Autodiscover.
4. Enter your password when prompted.
5. Complete the MFA challenge.
6. Wait for the initial mailbox synchronization to complete (can take 5–20 minutes depending on mailbox size).

### Manual Configuration (If Autodiscover Fails)
Use the following server settings:

| Setting | Value |
|---|---|
| Account Type | Microsoft 365 / Exchange |
| Incoming Server | `outlook.office365.com` |
| Port | 993 (IMAP) or 443 (Exchange) |
| Encryption | SSL/TLS |
| Outgoing Server | `smtp.office365.com` |
| SMTP Port | 587 |
| Authentication | OAuth2 / Modern Authentication |

---

## Section 2 — Common Outlook Errors

### "Cannot Connect to Server" / "Trying to Connect…"

**Causes:**
- Network/VPN not connected.
- Outlook profile is corrupted.
- M365 service issue.

**Resolution Steps:**
1. Check status page: `https://status.acmecorp.com` and `https://status.office.com`
2. Ensure you are on corporate network or connected to VPN.
3. Repair the Outlook profile:
   - Control Panel → Mail → Email Accounts → Repair
4. Create a new Outlook profile:
   - Control Panel → Mail → Show Profiles → Add
   - Set the new profile as default.
5. If the problem persists after profile recreation, raise an IT ticket.

---

### Autodiscover Error — "Allow this website to configure server settings?"

**What it means:** Outlook is trying to configure your account automatically but needs confirmation.

**Resolution Steps:**
1. Click **Allow** when prompted. This is safe for `autodiscover.acmecorp.com`.
2. If the dialog loops repeatedly, run the Microsoft Support and Recovery Assistant (SARA):
   > Download from: https://aka.ms/SaRA-EmailIssues
3. Alternatively, manually suppress the Autodiscover redirect:
   - Close Outlook
   - Open Registry Editor (`Win+R` → `regedit`)
   - Navigate to: `HKEY_CURRENT_USER\Software\Microsoft\Office\16.0\Outlook\AutoDiscover`
   - Create DWORD value: `PreferLocalXML` = `1`
   - Restart Outlook

---

### Outlook Stuck on "Loading Profile" at Startup

**Resolution Steps:**
1. Start Outlook in Safe Mode: Hold `Ctrl` while clicking the Outlook shortcut.
2. If Outlook starts normally in Safe Mode, a COM add-in is causing the problem:
   - File → Options → Add-ins → COM Add-ins → Manage → Go
   - Disable all add-ins one at a time to identify the culprit.
3. If Safe Mode also hangs, delete the Navigation Pane settings:
   - Close Outlook
   - Run: `outlook.exe /resetnavpane`
4. Repair the Office installation:
   - Control Panel → Programs → Microsoft 365 → Change → Quick Repair

---

### Emails Not Sending — Stuck in Outbox

**Causes:**
- Large attachment size exceeding the 25 MB limit.
- Corrupt draft email.
- Offline mode accidentally enabled.

**Resolution Steps:**
1. Check if Outlook is in Offline Mode: Send/Receive tab → confirm "Work Offline" is NOT highlighted.
2. Right-click the stuck email in Outbox → Delete. Re-compose and send.
3. Check attachment size. The maximum allowed size is **25 MB per message** for email. Use SharePoint or OneDrive for larger files.
4. Restart Outlook and try again.

---

### "Your Mailbox is Full" / Cannot Send or Receive

**What it means:** Your mailbox has reached the storage quota.

**Default Mailbox Quota:**
- Warning at **45 GB**
- Send/Receive blocked at **50 GB**

**Resolution Steps:**
1. Delete old emails from Inbox, Sent Items, and Junk.
2. Empty Deleted Items (Folder → Empty Folder).
3. Archive older emails:
   - File → Tools → Clean Up Old Items
   - Archive emails older than 1 year to a local `.pst` file.
4. Request a quota increase by raising an IT ticket (requires manager approval for increases above 50 GB).

---

### Cannot Open Attachments — "This file type is blocked"

**Cause:** The IT Security policy blocks certain dangerous file types (.exe, .bat, .vbs, .js) in email.

**Resolution Steps:**
1. Ask the sender to zip the file (`.zip`) and resend.
2. Alternatively, the sender can upload to SharePoint and share a link.
3. If you require a blocked file type for a legitimate business reason, raise a security exception request via IT ticket.

---

## Section 3 — Calendar Issues

### Meeting Invitations Not Showing in Calendar

**Resolution Steps:**
1. Check the **Scheduling Assistant** in the invitation to verify the invite was actually sent to you.
2. Search your inbox for the meeting subject — it may be filtered.
3. If you are a delegate calendar manager, verify you are viewing the correct calendar.
4. Clear the Outlook calendar cache:
   - File → Account Settings → Account Settings → Data Files
   - Delete the OST file (Outlook will recreate it — re-sync will take time).

### Free/Busy Information Not Showing

**Resolution Steps:**
1. Ensure you are connected to the corporate network or VPN.
2. In Outlook: File → Options → Calendar → Free/Busy Options → verify server URL is blank (for M365 it uses EWS automatically).
3. Run Autodiscover test:
   - Hold `Ctrl` + right-click Outlook tray icon → Test E-mail AutoConfiguration.
   - Verify Availability Service URL is present and shows `https://outlook.office365.com/`.

---

## Section 4 — Mobile Email Setup

### iOS (iPhone/iPad)

1. Settings → Mail → Accounts → Add Account → **Microsoft Exchange**.
2. Enter your corporate email address.
3. Tap **Sign In** (not Configure Manually).
4. You will be redirected to the Microsoft login page. Enter your corporate credentials.
5. Complete MFA.
6. Enable Mail, Contacts, Calendars, and Reminders as needed.
7. Tap **Save**.

### Android

1. Open the **Outlook** app (download from Google Play Store if not installed).
2. Tap **Add Account** → Enter corporate email address.
3. Follow the prompts — it will redirect to Microsoft login.
4. Complete MFA.
5. The account will sync within a few minutes.

**Note:** The personal Gmail or Samsung Email app may not work reliably with M365. The official **Microsoft Outlook** app is strongly recommended.

---

## Section 5 — Email Security Rules

- **Phishing:** Report suspicious emails using the **"Report Phishing"** button (Outlook add-in). Do NOT click links or open attachments in suspicious emails.
- **External Email Warning:** All emails from outside `@acmecorp.com` will show a yellow banner: **"EXTERNAL EMAIL — Exercise caution."**
- **Forwarding Rules:** Automatic email forwarding to external addresses is **disabled by IT policy** to prevent data leakage.
- **Shared Mailboxes:** Access to shared mailboxes (e.g., `support@acmecorp.com`) requires an IT ticket and manager approval.

---

## Section 6 — Escalation

If your email issue is unresolved after following the steps above, raise a ticket with:

- Your Employee ID
- Email address affected
- Exact error message (screenshot if possible)
- Steps already tried
- Whether the issue affects Outlook Desktop, OWA (web), or mobile

**Ticket Priority:** Medium  
**Expected Response Time:** 4 business hours  
**Support Contact:** `it-helpdesk@acmecorp.com`
