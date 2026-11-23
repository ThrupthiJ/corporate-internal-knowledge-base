# Deliverable 1: Detailed Architecture Diagram
## Corporate Internal Knowledge Base (Cloud File-Sharing Application)

### 1. High-Level Architecture Overview
The system is built on a 3-tier enterprise cloud architecture designed for high availability, zero-trust security boundaries, and strict departmental data segregation:
- **Presentation & Web Tier:** Nginx reverse proxy terminating TLS, routing traffic to a Python WSGI/Gunicorn application server hosted on an **AWS EC2 Virtual Machine**.
- **Application & RBAC Engine Tier:** Enforces fine-grained department-level access control, session authentication, keyword search indexation, and real-time audit event dispatching.
- **Object Storage Tier:** **Amazon S3** (`s3://corporate-knowledge-base-store/`) configured with prefix-isolated folders (`/hr/`, `/it/`, `/sales/`, `/shared/`), Server-Side Encryption (SSE-S3 / AES-256), and bucket policies.
- **Audit & Monitoring Tier:** Dual-layer logging comprising an immutable local SQLite audit database and integration with **Amazon CloudWatch Logs / AWS CloudTrail** for forensic non-repudiation.

---

### 2. Mermaid Architecture Diagram

```mermaid
flowchart TB
    subgraph Clients["Corporate End Users (Browser / API)"]
        U_HR["HR Department<br/>(hr_lead, hr_user)"]
        U_IT["IT Department<br/>(it_admin, it_specialist)"]
        U_SALES["Sales Department<br/>(sales_exec, sales_rep)"]
        U_AUDIT["Internal Auditor / CISO<br/>(auditor, admin)"]
    end

    subgraph AWS_Cloud["Amazon Web Services (AWS us-east-1 VPC)"]
        subgraph Compute["Cloud VM (Amazon EC2 Instance: t3.medium)"]
            Nginx["Nginx Reverse Proxy<br/>(Port 443 / SSL Termination)"]
            App["Python Flask Web Application<br/>(Gunicorn WSGI)"]
            RBAC["Access Control Decision Point (PDP)<br/>(Evaluates Least Privilege Policy)"]
            PEP["Policy Enforcement Point (PEP)<br/>(Blocks 403 Cross-Dept Access)"]
            AuditLogger["Security Audit Logger<br/>(Real-Time Event Stream)"]
        end

        subgraph IAM["AWS Identity & Access Management (IAM)"]
            InstanceProfile["EC2 IAM Instance Profile<br/>(arn:aws:iam::role/EC2-S3-KBAccess-Role)"]
            BucketPolicy["S3 Bucket Policy<br/>(Prefix-Level Authorization)"]
        end

        subgraph ObjectStorage["Object Storage (Amazon S3)"]
            S3["Bucket: s3://corporate-knowledge-base-store<br/>(SSE-S3 AES-256, Versioning Enabled)"]
            F_HR["Prefix /hr/<br/>HR Handbook, Benefits, Reviews"]
            F_IT["Prefix /it/<br/>Cloud Security Manual, Playbooks"]
            F_SALES["Prefix /sales/<br/>Sales Strategy, Pricing Matrix"]
            F_SHARED["Prefix /shared/<br/>Code of Conduct, Public Calendar"]
        end

        subgraph AuditSystem["Audit Trail & Compliance Engine"]
            SQLiteAudit["Local SQLite DB<br/>(audit_trail.db)"]
            CW_Logs["Amazon CloudWatch Logs / CloudTrail<br/>(/aws/ec2/corporate-kb/audit)"]
        end
    end

    %% User Flow
    U_HR -->|HTTPS| Nginx
    U_IT -->|HTTPS| Nginx
    U_SALES -->|HTTPS| Nginx
    U_AUDIT -->|HTTPS| Nginx

    %% Internal Processing Flow
    Nginx --> App
    App --> RBAC
    RBAC -->|Allow / Deny| PEP
    PEP -->|Log Event| AuditLogger
    
    %% AWS S3 Storage Flow
    PEP -->|Authorized API Calls| InstanceProfile
    InstanceProfile -->|boto3 SDK| S3
    S3 --- F_HR
    S3 --- F_IT
    S3 --- F_SALES
    S3 --- F_SHARED

    %% Audit Dispatch Flow
    AuditLogger --> SQLiteAudit
    AuditLogger --> CW_Logs
```

---

### 3. Component Details & Security Interactions

| Component | Cloud Resource | Security Role & Function |
| :--- | :--- | :--- |
| **Compute VM** | Amazon EC2 (`t3.medium`, Ubuntu 24.04 / Amazon Linux 2023) | Hosts web server, terminates TLS, enforces business logic, evaluates permissions. |
| **Reverse Proxy** | Nginx | Hides application server, enforces rate limiting, buffers requests, secures HTTP headers. |
| **IAM Instance Role** | `EC2-S3-KBAccess-Role` | Eliminates hardcoded AWS credentials on the VM; provides short-lived AWS STS tokens. |
| **Object Storage** | Amazon S3 Bucket | Stores departmental documents under dedicated prefixes. Enforces encryption at rest (AES-256). |
| **Access Control** | Flask RBAC + S3 Bucket Policy | Guarantees that HR cannot access IT or Sales data, preserving strict data confidentiality. |
| **Audit Trail** | SQLite + CloudWatch Logs | Captures all actions (Timestamp, User ID, Client IP, Target, Status) for forensic analysis. |
