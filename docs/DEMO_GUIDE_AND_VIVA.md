# Deliverable 7: Working Demo Guide & Presentation Script
## Scoring Breakdown: 15 Total Marks (10 for Work + 5 for Presentation)

This document provides a minute-by-minute live presentation guide and anticipated viva questions to ensure you maximize the 5 presentation marks.

---

### Part 1: How to Run the Demo Live
To launch the application on your computer or EC2 VM:

```bash
cd cloud-kb-app
python app.py
```
Open your browser at:
`http://127.0.0.1:5000` (or `http://<EC2-PUBLIC-IP>:5000`)

---

### Part 2: Step-by-Step 5-Minute Live Presentation Walkthrough

#### Step 1: System Introduction (1 Minute)
* **Action:** Start at the Login Page (`/login`) or Architecture Page (`/architecture`).
* **What to Say:**
  > *"Good morning/afternoon, Professor. Today we present Assignment 17: Corporate Internal Knowledge Base. Our objective is to build a secure cloud-native file-sharing application hosted on an AWS Cloud VM backed by Amazon S3 Object Storage.*
  > *In an enterprise, departments like HR, IT, and Sales handle sensitive data. HR holds compensation and employee grievances, IT holds network architectures and playbooks, and Sales holds confidential client pricing. Our system enforces strict fine-grained access control to prevent cross-department lateral movement while maintaining a company-wide shared knowledge base and an immutable security audit trail."*

#### Step 2: Role 1 — Human Resources Workflow (1 Minute)
* **Action:** Click **"HR Lead (Sarah Jenkins)"** on the login page or use the top-right switcher.
* **Demonstrate:**
  1. Point out the pink departmental badge.
  2. Click the **"HR"** tab: show that HR documents are fully accessible.
  3. Click **"View"** on `HR_Employee_Handbook_2026.txt`: show that the document loads with SSE-S3 encryption status.
  4. Click **"Shared"** tab: show that HR can also view the company-wide Code of Conduct.
* **What to Say:**
  > *"As Sarah from HR, I have full authorized access to HR documents and company-wide shared policies."*

#### Step 3: Demonstrating Security Violation & 403 Enforcement (1 Minute - High Impact!)
* **Action:** While still logged in as **HR Lead**, navigate to the **"Information Technology"** tab or click the red **"Attempt Access (403)"** button next to `Cloud_Infrastructure_Security_Manual.txt`.
* **Demonstrate:**
  1. The application immediately blocks access and renders the **HTTP 403 Forbidden** security alert.
  2. Show the alert message: *"Access Denied: User in department 'HR' cannot access 'IT' folder (Principle of Least Privilege violated)"*.
  3. Point out that the incident was intercepted and recorded in the audit trail.
* **What to Say:**
  > *"Notice what happens when an HR employee attempts to inspect a confidential IT security manual. The Policy Enforcement Point intercepts the request, blocks execution with an HTTP 403 Forbidden status, and instantly triggers an automated security alert."*

#### Step 4: Role 2 — Cross-Role Verification & Upload (1 Minute)
* **Action:** Switch role to **"IT Admin (Alex Rivera)"** via the top-right menu.
* **Demonstrate:**
  1. Notice that `Cloud_Infrastructure_Security_Manual.txt` is now unlocked and accessible.
  2. Click **"Upload Document"** in the top bar.
  3. Notice that the dropdown automatically scopes the target folder to `s3://.../it/` or `s3://.../shared/`.
  4. Try typing a query in the **Search Bar** (e.g., `"security"` or `"pricing"`): show that search results only return documents the active user is permitted to see.
* **What to Say:**
  > *"Now switching to Alex Rivera from IT, the IT security manual is authorized. When uploading new documents, the system restricts the target prefix to IT or Shared. Furthermore, our search engine enforces security scoping—an employee never sees search results for confidential files from other departments."*

#### Step 5: Compliance Auditor & Forensic Audit Trail (1 Minute)
* **Action:** Switch role to **"Auditor (Rachel Green)"** and click the **"Audit Trail"** tab.
* **Demonstrate:**
  1. Point out the KPI metrics: Total Events, Blocked Violations (403), Uploads, Downloads.
  2. Click **"Security Blocks Only"** filter: immediately show the 403 violation triggered in Step 3!
  3. Click **"Export Audit Logs (CSV)"**: show the browser downloading `audit_trail_export_....csv`.
  4. Navigate to the **"Architecture & RBAC Matrix"** tab to show the embedded Mermaid diagram and full access matrix.
* **What to Say:**
  > *"Finally, as an internal auditor, I have read-only inspection access and full visibility into the Security Audit Trail. Every login, upload, download, and unauthorized attempt is recorded with UTC timestamp, user ID, and source IP. We can export these logs to CSV for external compliance audits like SOC 2 or ISO 27001."*

---

### Part 3: Anticipated Viva Questions & Top-Scoring Answers

#### Q1: "How do you enforce folder permissions when S3 is a flat object store without real folders?"
* **Answer:**
  > *"S3 uses key prefixes delimited by forward slashes (`/`). In our architecture, permissions are enforced at two levels: First, within the application RBAC layer by validating the user's department against the target prefix. Second, in AWS IAM and S3 Bucket Policies using string condition keys like `s3:prefix` set to `["hr/*", "shared/*"]`. Requests specifying unauthorized prefixes are denied at the storage API layer."*

#### Q2: "How do you secure credentials on the EC2 Virtual Machine?"
* **Answer:**
  > *"We avoid storing static AWS access keys or secrets in environment files or source code. Instead, we use an **IAM Instance Profile** attached to the EC2 instance (`EC2-S3-KBAccess-Role`). AWS automatically manages and rotates short-lived STS credentials for the VM, adhering to cloud security best practices."*

#### Q3: "What prevents someone from tampering with the audit logs?"
* **Answer:**
  > *"Audit logs are dual-streamed. Locally, they are written to an append-only file and SQLite database. In AWS production, they are streamed to Amazon CloudWatch Logs and can be archived to an S3 bucket configured with **S3 Object Lock** in Compliance Mode (WORM: Write Once, Read Many), making logs immutable and tamper-proof even by root administrators."*

#### Q4: "How is data protected in transit and at rest?"
* **Answer:**
  > *"**In Transit:** All communications between clients, Nginx, and the web application use TLS 1.3 encryption (HTTPS). Furthermore, the S3 bucket policy includes a condition denying any requests where `aws:SecureTransport` is false.*
  > ***At Rest:** Files in S3 are protected using Server-Side Encryption with Amazon S3 managed keys (`SSE-S3` / AES-256), configured as the default bucket encryption standard."*
