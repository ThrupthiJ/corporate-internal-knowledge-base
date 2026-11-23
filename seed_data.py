import os
import shutil
from config import Config, DEPARTMENTS, USERS
from storage import get_storage
from audit import init_audit_db, log_event

def seed():
    print("[*] Initializing audit database...")
    init_audit_db()
    
    storage, engine_name = get_storage()
    print(f"[*] Active Storage Engine: {engine_name}")
    
    base_sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_docs')
    
    # 1. Populate storage folders with departmental sample documents
    print("[*] Seeding departmental documents...")
    for dept in ['hr', 'it', 'sales', 'shared']:
        dept_dir = os.path.join(base_sample_dir, dept)
        if not os.path.exists(dept_dir):
            continue
            
        for fname in os.listdir(dept_dir):
            src_file = os.path.join(dept_dir, fname)
            if os.path.isfile(src_file):
                with open(src_file, 'rb') as f:
                    content = f.read()
                storage.upload_file(dept, fname, content)
                print(f"  -> Uploaded [{dept.upper()}]: {fname}")
                
                # Log upload event in audit trail
                uploader = USERS.get(f"{dept}_lead") or USERS.get('admin')
                log_event(
                    user=uploader,
                    action='UPLOAD_DOCUMENT',
                    target_dept=dept,
                    resource_name=fname,
                    status='SUCCESS',
                    client_ip='10.0.1.45',
                    details=f"Initial seed upload of departmental document '{fname}' to s3://{Config.S3_BUCKET_NAME}/{dept}/"
                )

    # 2. Add realistic past audit logs for security demonstration
    print("[*] Generating realistic security audit history...")
    
    # Successful login & search by HR
    log_event(
        user=USERS['hr_lead'],
        action='LOGIN',
        target_dept='system',
        resource_name='AuthGateway',
        status='SUCCESS',
        client_ip='192.168.1.102',
        details='Successful MFA authenticated session initiated for Sarah Jenkins (HR)'
    )
    log_event(
        user=USERS['hr_lead'],
        action='VIEW_DOCUMENT',
        target_dept='hr',
        resource_name='HR_Employee_Handbook_2026.txt',
        status='SUCCESS',
        client_ip='192.168.1.102',
        details='Read access granted for HR internal document'
    )
    
    # Security Alert: Simulated Unauthorized Cross-Department Access Attempt
    # HR Lead attempts to download confidential IT Security Manual -> Blocked!
    log_event(
        user=USERS['hr_user'],
        action='UNAUTHORIZED_ACCESS_ATTEMPT',
        target_dept='it',
        resource_name='Cloud_Infrastructure_Security_Manual.txt',
        status='BLOCKED_403',
        client_ip='192.168.1.108',
        details='SECURITY ALERT: Lateral access violation! HR user attempted to access restricted IT document. Policy: Principle of Least Privilege.'
    )
    
    # Sales Rep attempts to download HR Salary Guide -> Blocked!
    log_event(
        user=USERS['sales_rep'],
        action='UNAUTHORIZED_ACCESS_ATTEMPT',
        target_dept='hr',
        resource_name='Benefits_and_Compensation_Guide.txt',
        status='BLOCKED_403',
        client_ip='192.168.1.215',
        details='SECURITY ALERT: Sales employee attempted unauthorized read of confidential HR compensation structure. Request intercepted.'
    )
    
    # Auditor inspection
    log_event(
        user=USERS['auditor'],
        action='AUDIT_INSPECTION',
        target_dept='all',
        resource_name='FullAuditLogReport',
        status='SUCCESS',
        client_ip='10.0.4.12',
        details='Compliance audit trail inspection conducted by internal auditor Rachel Green.'
    )

    print("[+] Seeding completed successfully! Storage folders, files, and audit trail are ready.")

if __name__ == '__main__':
    seed()
