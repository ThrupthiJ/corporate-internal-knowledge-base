# Corporate Internal Knowledge Base - Cloud File Sharing Application
## Assignment 17: Cloud Computing

A secure, multi-department enterprise file-sharing and knowledge repository built for **AWS Cloud VM (Amazon EC2)** and **Object Storage (Amazon S3)**.

---

### Key Features
- **Department Document Upload:** Dedicated storage prefixes for **HR**, **IT**, and **Sales**.
- **Knowledge Sharing:** Company-wide `/shared/` folder accessible to all verified employees.
- **Document Search:** Instant keyword search scoped dynamically by user permissions.
- **Fine-Grained Access Control:** Strict Role-Based Access Control (RBAC) preventing cross-department lateral movement.
- **Audit Trails:** Real-time logging of logins, uploads, downloads, searches, and unauthorized access attempts (HTTP 403) with source IP and timestamps.
- **Dual-Mode Storage Engine:** Supports AWS S3 natively via `boto3` and includes a zero-dependency S3-mirror storage backend for instant offline demonstration.

---

### Project Structure
```
cloud-kb-app/
├── app.py                      # Main Flask application with RBAC & routes
├── config.py                   # Configuration, user directory, and RBAC matrix
├── storage.py                  # Dual-mode storage engine (AWS S3 & Local Mirror)
├── audit.py                    # Real-time audit trail engine (SQLite & JSON stream)
├── seed_data.py                # Pre-populates sample documents and audit history
├── test_app.py                 # Automated security unit test suite
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── setup_aws.py                # Automated AWS S3 & bucket policy provisioning script
├── templates/                  # Frontend HTML templates (Tailwind CSS & Lucide Icons)
│   ├── base.html               # Base layout & instant role switcher
│   ├── index.html              # Document explorer, search, and upload modal
│   ├── login.html              # Login portal with 1-click test credentials
│   ├── view_doc.html           # Document viewer
│   ├── access_denied.html      # 403 Security violation alert screen
│   ├── audit.html              # Security Audit Trail dashboard & CSV export
│   └── architecture.html       # Architecture diagram & Access Matrix tab
├── sample_docs/                # Deliverable 3: Pre-created sample documents
│   ├── hr/                     # HR Handbook, Benefits Guide, Appraisal Form
│   ├── it/                     # Cloud Architecture Manual, Playbook, VPN Policy
│   ├── sales/                  # Sales Strategy, Pricing Matrix, Pitch Deck
│   └── shared/                 # Code of Conduct, Holiday Calendar, KB Guide
├── aws/                        # Cloud deployment templates
│   ├── s3_bucket_policy.json   # AWS S3 Bucket Policy with prefix isolation
│   ├── ec2_userdata.sh         # EC2 VM automatic provisioning bootstrap script
│   └── iam_policies/           # IAM Policies for HR, IT, Sales, and EC2 Role
└── docs/                       # Assignment Deliverables 1 through 8
    ├── ARCHITECTURE_DIAGRAM.md # Deliverable 1: Detailed architecture diagram
    ├── ACCESS_CONTROL_MATRIX.md# Deliverable 2: Department access control matrix
    ├── FOLDER_STRUCTURE_GUIDE.md# Deliverable 4: Folder structure & screenshots
    ├── USER_GROUP_CONFIG.md    # Deliverable 6: IAM users & groups configuration
    ├── DEMO_GUIDE_AND_VIVA.md  # Deliverable 7: 5-minute presentation script & viva Q&A
    └── FINAL_PROJECT_REPORT.md # Deliverable 8: 10-mark Project Report & Security Analysis
```

---

### Quick Start Guide

#### 1. Run Locally / On VM
```bash
python seed_data.py
python app.py
```
Open your browser at:
`http://127.0.0.1:5000`

#### 2. Run Automated Security Unit Tests
```bash
python test_app.py
```

#### 3. Test Credentials Quick Reference
| Username | Password | Role / Department | Permissions |
| :--- | :--- | :--- | :--- |
| `hr_lead` | `hr123` | HR Lead (Human Resources) | Full HR + Shared |
| `it_admin` | `it123` | Cloud Security Engineer (IT) | Full IT + Shared |
| `sales_exec` | `sales123` | VP of Sales (Sales) | Full Sales + Shared |
| `auditor` | `audit123` | Compliance Auditor | Read-Only all + Audit Logs |
| `admin` | `admin123` | CISO / Super Admin | Full System Access |
