# Deliverable 6: User and Group Configuration
## Corporate Internal Knowledge Base

### 1. Identity & Departmental User Directory
The application provisions distinct user personas across three operational departments (HR, IT, Sales) and two administrative/compliance roles:

| Username | Full Name | Department | Role Tier | Primary Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **`hr_lead`** | Sarah Jenkins | Human Resources | `department_lead` | Full Read/Write/Delete on `/hr/` & Read/Write on `/shared/`. |
| **`hr_user`** | Michael Chang | Human Resources | `department_member`| Read/Write on `/hr/` & `/shared/`. |
| **`it_admin`** | Alex Rivera | Information Technology | `department_lead` | Full Read/Write/Delete on `/it/` & Read/Write on `/shared/`. |
| **`it_specialist`**| David Kim | Information Technology | `department_member`| Read/Write on `/it/` & `/shared/`. |
| **`sales_exec`** | Elena Rostova | Sales & Commercial | `department_lead` | Full Read/Write/Delete on `/sales/` & Read/Write on `/shared/`. |
| **`sales_rep`** | Jordan Lee | Sales & Commercial | `department_member`| Read/Write on `/sales/` & `/shared/`. |
| **`auditor`** | Rachel Green | Internal Compliance | `auditor` | Read-only inspection of all files + Full access to Audit Trail. |
| **`admin`** | CISO | Security Operations | `superadmin` | Global administrative control, audit export, and system configuration. |

---

### 2. AWS IAM Group Architecture
To enforce identity controls at the AWS cloud layer, three IAM User Groups and one IAM Role are defined:

#### Group 1: `HR-Department-Group`
- **Assigned Users:** `hr_lead`, `hr_user`
- **Managed Policy:** `aws/iam_policies/hr_group_policy.json`
- **Permissions:**
  - `s3:ListBucket` with condition `s3:prefix` in `["", "hr/*", "shared/*"]`.
  - `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on `arn:aws:s3:::corporate-knowledge-base-store/hr/*` and `shared/*`.
  - **Explicit Deny** on `arn:aws:s3:::corporate-knowledge-base-store/it/*` and `sales/*`.

#### Group 2: `IT-Department-Group`
- **Assigned Users:** `it_admin`, `it_specialist`
- **Managed Policy:** `aws/iam_policies/it_group_policy.json`
- **Permissions:**
  - `s3:ListBucket` with condition `s3:prefix` in `["", "it/*", "shared/*"]`.
  - `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on `arn:aws:s3:::corporate-knowledge-base-store/it/*` and `shared/*`.
  - **Explicit Deny** on `arn:aws:s3:::corporate-knowledge-base-store/hr/*` and `sales/*`.

#### Group 3: `Sales-Department-Group`
- **Assigned Users:** `sales_exec`, `sales_rep`
- **Managed Policy:** `aws/iam_policies/sales_group_policy.json`
- **Permissions:**
  - `s3:ListBucket` with condition `s3:prefix` in `["", "sales/*", "shared/*"]`.
  - `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on `arn:aws:s3:::corporate-knowledge-base-store/sales/*` and `shared/*`.
  - **Explicit Deny** on `arn:aws:s3:::corporate-knowledge-base-store/hr/*` and `it/*`.

#### Role 4: `EC2-S3-KBAccess-Role` (Compute Instance Profile)
- **Attached To:** Amazon EC2 Virtual Machine instance hosting the application.
- **Trust Relationship:** `ec2.amazonaws.com`.
- **Purpose:** Enables the application server to securely dispatch S3 API calls and forward audit trail entries to Amazon CloudWatch without hardcoding static API access keys in configuration files.
