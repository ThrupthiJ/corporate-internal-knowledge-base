# Deliverable 2: Department Access Control Matrix (RBAC)
## Corporate Internal Knowledge Base

### 1. Security Principle: Least Privilege & Departmental Isolation
The access control framework operates under the **Principle of Least Privilege (PoLP)**:
- Users are granted only the minimum permissions necessary to perform their legitimate job functions.
- Cross-department access between **HR**, **IT**, and **Sales** is blocked by default with an **Explicit Deny**.
- A common **Shared** folder allows company-wide knowledge distribution without compromising confidential departmental files.
- Dedicated compliance roles (**Auditor**) possess read-only visibility for security reviews, preventing accidental or malicious modification.

---

### 2. Department Access Control Matrix

| Role Name | Department | HR Folder (`/hr/`) | IT Folder (`/it/`) | Sales Folder (`/sales/`) | Shared Folder (`/shared/`) | Audit Trail Dashboard |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`hr_lead`** | Human Resources | **Read / Write / Delete** | ❌ **DENY (403)** | ❌ **DENY (403)** | **Read / Write** | ❌ **DENY (403)** |
| **`hr_user`** | Human Resources | **Read / Write** | ❌ **DENY (403)** | ❌ **DENY (403)** | **Read / Write** | ❌ **DENY (403)** |
| **`it_admin`** | Information Technology | ❌ **DENY (403)** | **Read / Write / Delete** | ❌ **DENY (403)** | **Read / Write** | ❌ **DENY (403)** |
| **`it_specialist`**| Information Technology | ❌ **DENY (403)** | **Read / Write** | ❌ **DENY (403)** | **Read / Write** | ❌ **DENY (403)** |
| **`sales_exec`** | Sales & Commercial | ❌ **DENY (403)** | ❌ **DENY (403)** | **Read / Write / Delete** | **Read / Write** | ❌ **DENY (403)** |
| **`sales_rep`** | Sales & Commercial | ❌ **DENY (403)** | ❌ **DENY (403)** | **Read / Write** | **Read / Write** | ❌ **DENY (403)** |
| **`auditor`** | Compliance & Audit | **Read-Only** | **Read-Only** | **Read-Only** | **Read-Only** | **Read / Export CSV** |
| **`admin`** | IT Sec / CISO | **Full Admin** | **Full Admin** | **Full Admin** | **Full Admin** | **Full Admin & Purge** |

---

### 3. Action-to-Permission Mapping Table

| User Action | HTTP Method | Route | Permission Evaluation Function | Expected Outcome if Unauthorized |
| :--- | :--- | :--- | :--- | :--- |
| **Search Documents** | `GET` | `/?q=query` | `can_access_folder(user, dept, 'read')` | Filtered out from results; no error exposed. |
| **View Document Inline** | `GET` | `/view/<dept>/<file>` | `can_access_folder(user, dept, 'read')` | **HTTP 403 Forbidden**, Security Alert modal rendered, `BLOCKED_403` audit event logged. |
| **Download Document** | `GET` | `/download/<dept>/<file>`| `can_access_folder(user, dept, 'read')` | **HTTP 403 Forbidden**, download intercepted, audit event logged. |
| **Upload Document** | `POST` | `/upload` | `can_access_folder(user, dept, 'upload')` | Rejected with flash error; upload blocked. |
| **Delete Document** | `POST` | `/delete/<dept>/<file>` | `role in ['department_lead', 'superadmin']` | **HTTP 403 Forbidden**; deletion denied. |
| **Export Audit Logs** | `GET` | `/audit/export/csv` | `can_view_audit_trail(user)` | Redirected to index with warning. |

---

### 4. Enforcement Mechanism
Permissions are enforced at two independent layers (**Defense in Depth**):
1. **Application Layer (PEP - Policy Enforcement Point):** Evaluated inside `config.py:can_access_folder()`. Any unauthorized attempt immediately raises an HTTP 403 status and generates a high-severity security alert.
2. **Cloud Storage Layer (S3 Bucket Policy & IAM):** AWS S3 bucket policies define explicit denies for any request carrying an IAM principal not belonging to the targeted folder prefix. Even if application credentials were bypassed, direct AWS S3 calls would still fail.
