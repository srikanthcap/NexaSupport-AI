# Password Reset & SSO Troubleshooting Guide
**Document ID:** KB-AUTH-003  
**Category:** Identity & Access Management  
**Last Updated:** 2024-01-15  
**Owner:** IT Security & IAM Team

---

## Overview

Acme Corp uses **Microsoft Active Directory (AD)** as the central identity provider for all corporate accounts. **Single Sign-On (SSO)** is implemented via **Microsoft Azure AD (Entra ID)** using the SAML 2.0 / OpenID Connect protocols. This means a single set of corporate credentials provides access to all connected applications (JIRA, SharePoint, Workday, Salesforce, etc.) after authenticating once.

**Multi-Factor Authentication (MFA)** is mandatory for all employees accessing corporate resources remotely.

---

## Section 1 — Password Policy

### Requirements
- Minimum **12 characters**
- Must include at least **1 uppercase letter**
- Must include at least **1 lowercase letter**
- Must include at least **1 number**
- Must include at least **1 special character** (e.g., `!@#$%^&*`)
- Cannot reuse the **last 12 passwords**
- Password expires every **90 days**

### Expiry Notifications
- You will receive email reminders at **14 days, 7 days, and 1 day** before expiry.
- Outlook and Windows will also display a notification when you log in within 14 days of expiry.

---

## Section 2 — How to Change Your Password (When It Still Works)

### Option A — Windows (Ctrl+Alt+Delete)
1. Press `Ctrl + Alt + Delete` on your work device.
2. Select **Change a password**.
3. Enter your **current password** once, then your **new password** twice.
4. Press the right arrow or Enter. Windows will confirm the change.

### Option B — OWA (Outlook Web Access)
1. Go to `https://mail.acmecorp.com`
2. Click your profile picture (top-right) → **View account**.
3. Under Security → **Change password**.
4. Follow the prompts.

### Option C — Self-Service Password Reset Portal (SSPR)
Available even when NOT connected to corporate network or VPN:
> **https://passwordreset.acmecorp.com**

Requirements to use SSPR:
- You must have registered at least **2 authentication methods** (mobile phone number, alternate email, or authenticator app) during onboarding.

---

## Section 3 — Forgotten / Expired Password (Account Locked Out)

### If You Can Still Receive Email or SMS

1. Go to: **https://passwordreset.acmecorp.com**
2. Click **I forgot my password**.
3. Enter your corporate email address.
4. Choose a verification method:
   - Text message to your registered mobile number
   - Call to your registered phone number
   - Notification via the Acme Authenticator app
5. Complete the verification.
6. Set a new password meeting the policy requirements.
7. Wait **5 minutes** for the change to propagate across all systems.
8. Reconnect to VPN and log in to applications.

### If You Have Lost Access to All MFA Methods (Locked Out Completely)

You must contact IT Helpdesk **in person or by phone**. For security reasons, identity cannot be verified via email when you are completely locked out.

**Contact Options:**
- **Phone:** `+1-800-IT-ACME Ext. 1001` (available 8 AM – 6 PM IST, Mon–Fri)
- **Walk-in:** IT Support Desk, Floor 3, Building A, Head Office
- **Emergency (after hours):** `+1-800-IT-ACME Ext. 9999`

You will need to provide:
- Employee ID
- Date of birth
- Manager's name

IT will reset your account and issue a **temporary password** valid for 24 hours. You must change it immediately upon first login.

---

## Section 4 — Account Lockout

### Automatic Lockout Policy
- After **5 consecutive failed login attempts**, your account is locked for **30 minutes**.
- After the 30-minute period, the account automatically unlocks.
- You can also ask IT Helpdesk to unlock it immediately.

### How to Check If Your Account Is Locked

Symptom: You enter your correct password but get "Invalid credentials" or "Account locked" message.

1. Wait 30 minutes and retry.
2. Or call IT Helpdesk with your Employee ID for immediate unlock.

---

## Section 5 — SSO Issues

### "Cannot Access Application via SSO" / Redirect Loop

**What it means:** The application's SAML/OIDC configuration with Azure AD is misconfigured, or your session token has expired.

**Resolution Steps:**
1. Clear your browser cache and cookies:
   - Chrome: `Ctrl+Shift+Delete` → Clear browsing data → Last 24 hours → Cached images, Cookies
2. Open the application in a **Private/Incognito** window.
3. Sign out completely from `https://myapps.microsoft.com` (the Azure AD application portal), then sign back in.
4. Try a different browser (Edge, Chrome, Firefox).
5. If the issue is in a specific application only (e.g., JIRA):
   - The application's SSO configuration may need to be refreshed by an IT admin.
   - Raise an IT ticket with the application name and exact error message shown.

### "You Are Not Authorized to Access This Application"

**What it means:** Your account is not in the correct **security group** for that application.

**Resolution Steps:**
1. Confirm with your manager that you have received approval to access the application.
2. Raise an IT Access Request ticket with:
   - Application name
   - Business justification
   - Manager approval email (screenshot or CC)
3. Access provisioning typically takes **1–2 business days**.

### "AADSTS Error Codes" (Azure AD Error Codes)

| Error Code | Meaning | Action |
|---|---|---|
| AADSTS50126 | Invalid username/password | Check credentials or reset password |
| AADSTS50076 | MFA required | Complete MFA challenge |
| AADSTS50105 | User not assigned to the application | Request access via IT ticket |
| AADSTS70011 | Invalid scope requested | Application config issue — raise IT ticket |
| AADSTS900144 | Request body must contain parameter | Browser issue — clear cache and retry |

---

## Section 6 — MFA Enrollment & Issues

### First-Time MFA Setup

1. Go to: **https://aka.ms/mfasetup**
2. Sign in with your corporate credentials.
3. Follow the wizard to add at least **2 verification methods**:
   - Mobile phone number (SMS)
   - Acme Authenticator app (most secure — recommended)
   - Alternate email address

### Acme Authenticator App Setup

1. Download **Microsoft Authenticator** from App Store or Google Play.
2. Open the app → Add account → Work or school account.
3. At the SSPR setup page (`https://aka.ms/mfasetup`), select **Authenticator app** and scan the QR code.
4. Verify with a test code.

### MFA Not Working — Code Invalid

**Causes:**
- Device clock is out of sync (TOTP codes are time-based and fail if clock differs by > 30 seconds).

**Resolution:**
1. On your phone, go to Settings → General → Date & Time → Enable "Set Automatically."
2. Open Microsoft Authenticator → three dots menu → Time correction for codes → Sync now.
3. Retry the code.

### Lost MFA Device / New Phone

1. If you still have your old device, transfer the accounts first using Microsoft Authenticator's backup/restore feature.
2. If old device is unavailable, contact IT Helpdesk to **reset your MFA registration**.
3. After reset, complete MFA setup again at `https://aka.ms/mfasetup`.

---

## Section 7 — Escalation

For unresolved identity/access issues, raise an IT ticket with:

- Employee ID
- Application name (if SSO issue)
- Exact error message or AADSTS code
- Screenshot of error page
- Whether password change or MFA reset was attempted

**Ticket Priority:** High (account lockout blocks work)  
**Expected Response Time:** 2 business hours  
**IAM Team Contact:** `iam-team@acmecorp.com`
