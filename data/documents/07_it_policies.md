# IT Policies & Security Guidelines
**Document ID:** KB-POL-007  
**Category:** IT Policy / Security  
**Last Updated:** 2024-01-15  
**Owner:** IT Security & Compliance Team

---

## Overview

This document outlines the key IT policies at Acme Corp that every employee must be aware of. Compliance is mandatory. Violations may result in disciplinary action up to and including termination and legal liability, depending on severity.

If you have questions about any policy, contact the IT Security team at `security@acmecorp.com`.

---

## Section 1 — Acceptable Use Policy (AUP)

### Permitted Use

Corporate IT resources (laptops, network, email, applications) are provided for **legitimate business purposes**. Limited and reasonable personal use is tolerated but must not:

- Interfere with work duties.
- Consume excessive bandwidth (e.g., streaming media during business hours).
- Violate any other policy in this document.

### Prohibited Activities

Employees may NOT use corporate IT resources to:

- Access, download, or distribute illegal content.
- Install unauthorized software.
- Connect unauthorized storage devices.
- Bypass security controls (VPN, firewall, proxy, DLP).
- Share corporate credentials with anyone (including IT staff — IT will NEVER ask for your password).
- Use company email for personal business or commercial activity.
- Access competitor systems, personal file-sharing sites (torrents), or anonymization services (Tor, proxy bypass tools).
- Post confidential company information on social media or external forums.

### Monitoring

Employees should be aware that Acme Corp monitors network traffic, email, and device activity in accordance with applicable law. Use of corporate IT systems implies consent to monitoring.

---

## Section 2 — Data Classification Policy

All Acme Corp data is classified into four tiers:

| Classification | Description | Examples | Handling |
|---|---|---|---|
| **Public** | Approved for external distribution | Press releases, public website content | No restrictions |
| **Internal** | For employee use only | Policies, procedures, project plans | Do not share externally without approval |
| **Confidential** | Sensitive business information | Financial reports, customer PII, HR data | Encrypt in transit and at rest; share only on need-to-know basis |
| **Restricted** | Highest sensitivity | Mergers/acquisitions info, source code, authentication secrets | Strict access controls; never email; use approved secure share methods only |

### Handling Rules Summary

- **Do NOT email Confidential or Restricted data.** Use SharePoint with appropriate permissions or the approved secure file transfer portal (`securetransfer.acmecorp.com`).
- **Do NOT store Confidential or Restricted data on personal devices**, cloud drives (Google Drive, Dropbox, personal OneDrive), or unauthorized USB drives.
- **If you receive Confidential or Restricted data that you should not have access to**, notify IT Security immediately at `security@acmecorp.com`.

---

## Section 3 — IT Incident Severity Definitions

All IT issues are classified by severity to prioritize response:

| Severity | Definition | Examples | Response SLA |
|---|---|---|---|
| **SEV-1 (Critical)** | Complete business disruption affecting multiple users or critical systems | Entire office network down, email service outage, production system failure | 30 minutes |
| **SEV-2 (High)** | Significant impact on individual or small group productivity | Single user cannot log in, VPN down for remote worker, application inaccessible | 2 business hours |
| **SEV-3 (Medium)** | Moderate issue with a workaround available | Printer not working, slow application performance, peripheral not detected | 4 business hours |
| **SEV-4 (Low)** | Minor issue or informational request | Password change guidance, software information request, how-to queries | 1 business day |

### How to Report an Incident

1. **Self-service first:** Check this knowledge base and attempt the documented resolution steps.
2. **IT Helpdesk:** Call `+1-800-IT-ACME Ext. 1001` or email `it-helpdesk@acmecorp.com`.
3. **Create a ticket:** Use the IT Portal at `https://itportal.acmecorp.com` for non-urgent requests.
4. **Emergency escalation:** For SEV-1 incidents during non-business hours, call `+1-800-IT-ACME Ext. 9999`.

---

## Section 4 — BYOD (Bring Your Own Device) Policy

**Personal devices may NOT be connected to the `ACME-CORP` corporate Wi-Fi network.**

Personal devices may use the **`ACME-GUEST`** Wi-Fi network for internet access only. Guest network does not have access to internal resources.

**Mobile email on personal devices:**

Employees may access corporate email on personal mobile devices if:

1. The device is enrolled in **Intune Mobile Device Management (MDM)** for the email profile only (Intune will NOT manage personal apps or data).
2. The device has a screen lock (PIN / biometric) enabled.
3. The Microsoft Outlook app is used (native mail apps are NOT permitted for corporate email on personal devices).

To enroll your personal device, visit: `https://enroll.acmecorp.com`

---

## Section 5 — Password Policy Summary

(Full details in KB-AUTH-003)

- Minimum 12 characters with uppercase, lowercase, number, and special character.
- 90-day expiry.
- No reuse of last 12 passwords.
- Account lockout after 5 failed attempts (30-minute auto-unlock).
- **Never share your password with anyone, including IT staff.**
- Use the LastPass Enterprise password manager for all non-corporate system passwords.

---

## Section 6 — Remote Work Security Policy

Employees working remotely must:

1. **Always connect via GlobalProtect VPN** when accessing internal resources.
2. Use only **corporate-managed devices** for work. Personal laptops connecting to internal systems are not permitted.
3. Ensure their home Wi-Fi router is protected with **WPA2 or WPA3 encryption** and a strong password.
4. Not allow family members to use corporate devices.
5. Lock the screen (`Win+L` / `Cmd+Ctrl+Q`) whenever stepping away from the device.
6. Never conduct sensitive calls or meetings in public spaces where the screen or conversation may be overheard.
7. Use a **privacy screen filter** on laptops when working in public spaces (coffee shops, airports).

---

## Section 7 — Software & License Compliance

- Only **approved software** (listed in KB-SW-004) may be installed on corporate devices.
- All software licenses are tracked in the IT Asset Management system.
- Using unlicensed or pirated software on corporate devices is prohibited and may expose the company to legal liability.
- AI/LLM tools (ChatGPT, Copilot, Claude, etc.): Only Microsoft Copilot for M365 is approved for business use. Do NOT enter confidential or customer data into external AI tools. See the AI Acceptable Use addendum for details.

---

## Section 8 — Endpoint Security

All corporate managed endpoints have:

- **Microsoft Defender for Endpoint** — antivirus, EDR, threat detection
- **BitLocker Encryption** — full disk encryption (recovery key stored in Azure AD)
- **Microsoft Intune** — device management, policy enforcement, remote wipe capability
- **DLP (Data Loss Prevention)** agent — prevents unauthorized data transfer via USB, email, or upload

**If a device is lost or stolen:**

1. Report immediately to your manager and IT Security.
2. Call `+1-800-IT-ACME Ext. 9999` (24/7 emergency line).
3. IT will remotely wipe the device within 30 minutes of notification.
4. BitLocker encryption ensures data is protected even if the device is physically accessed.

---

## Section 9 — Phishing & Social Engineering Awareness

- Acme Corp will **NEVER** send you an email asking for your password, credit card number, or other sensitive information.
- IT staff will **NEVER** ask for your password over email, phone, or in person.
- Be suspicious of urgent emails claiming your account will be suspended, locked, or require immediate action.
- Report suspicious emails using the **Report Phishing** button in Outlook.
- If you accidentally clicked a phishing link or entered credentials on a suspicious site, contact IT Security immediately — do not wait.

---

## Section 10 — Compliance & Audits

Acme Corp is subject to:

- **ISO 27001** — Information Security Management
- **SOC 2 Type II** — Security, Availability, Confidentiality controls
- **GDPR** — EU data privacy regulation (relevant for EU employee and customer data)
- **PCI-DSS** — Payment Card Industry data security (for teams handling payment data)

IT Security conducts quarterly access reviews. Employees who no longer require access to specific systems will have that access revoked.

For compliance-related questions, contact `compliance@acmecorp.com`.
