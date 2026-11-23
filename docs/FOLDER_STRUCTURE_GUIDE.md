# Deliverable 4: Folder Structure Guide & Screenshot Documentation
## Corporate Internal Knowledge Base

### 1. Object Storage Prefix Architecture
In cloud object storage (such as Amazon S3), directories do not exist as physical filesystems; instead, they are modeled using **Key Prefixes** delimited by forward slashes (`/`).

Our application provisions and manages the following prefix hierarchy inside `s3://corporate-knowledge-base-store/`:

```
s3://corporate-knowledge-base-store/
│
├── hr/                                          [Human Resources Department Restricted]
│   ├── Benefits_and_Compensation_Guide.txt     (Confidential Salary & Benefits Tiers)
│   ├── HR_Employee_Handbook_2026.txt           (Employee Policies & Conduct)
│   └── Performance_Appraisal_Form.txt          (Appraisal Benchmark & Rating System)
│
├── it/                                          [IT & Security Operations Restricted]
│   ├── Cloud_Infrastructure_Security_Manual.txt(VPC, EC2 Hardening & Encryption Specs)
│   ├── Incident_Response_Playbook.txt          (NIST SP 800-61 SecOps Escalation)
│   └── Network_Access_VPN_Policy.txt           (Zero-Trust MFA & Split-Tunneling Rules)
│
├── sales/                                       [Sales & Commercial Restricted]
│   ├── Client_Pricing_Matrix_Confidential.txt  (Proprietary Pricing & Margin Floors)
│   ├── Product_Feature_Pitch_Deck.txt          (Competitive Battlecards & Pitch Copy)
│   └── Q4_Enterprise_Sales_Strategy.txt        (Pipeline Targets & Enterprise Deals)
│
└── shared/                                      [Company-Wide Knowledge Repository]
    ├── 2026_Annual_Holiday_Calendar.txt        (Official Corporate Holidays)
    ├── Corporate_Code_of_Conduct.txt           (Ethics, Anti-Bribery, Whistleblower)
    └── Internal_Knowledge_Base_Guide.txt       (KB User Guide & FAQs)
```

---

### 2. Screenshots Required for Final Submission Report
For your final report submission and viva, include the following 3 screenshots:

#### Screenshot 4.1: AWS Management Console (S3 Bucket Overview)
- **Where to capture:** AWS Management Console -> Amazon S3 -> Buckets -> `corporate-knowledge-base-store`.
- **What it displays:** The 4 top-level departmental folders (`hr/`, `it/`, `sales/`, `shared/`).
- **Command to inspect via AWS CLI:**
  ```bash
  aws s3 ls s3://corporate-knowledge-base-store/
  ```
  *Expected Output:*
  ```
     PRE hr/
     PRE it/
     PRE sales/
     PRE shared/
  ```

#### Screenshot 4.2: Department Subfolder Contents (e.g. `/hr/`)
- **Where to capture:** AWS S3 Console inside the `hr/` folder, or in the web application under the "Human Resources" tab.
- **What it displays:** The 3 sample documents (`Benefits_and_Compensation_Guide.txt`, `HR_Employee_Handbook_2026.txt`, `Performance_Appraisal_Form.txt`).
- **Command to inspect via AWS CLI:**
  ```bash
  aws s3 ls s3://corporate-knowledge-base-store/hr/
  ```

#### Screenshot 4.3: Local Storage / VM Mirror Verification
- **Where to capture:** Inside your EC2 VM terminal or local test folder:
  ```powershell
  Get-ChildItem -Recurse .\bucket_storage\corporate-knowledge-base-store
  ```
  or on Linux EC2:
  ```bash
  tree /opt/cloud-kb-app/bucket_storage/corporate-knowledge-base-store/
  ```
