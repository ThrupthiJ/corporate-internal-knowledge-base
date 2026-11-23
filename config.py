import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'corporate-kb-dev-secret-key-2026')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'corporate-knowledge-base-store')
    AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Storage Backend Mode: 'auto', 's3', or 'local'
    STORAGE_MODE = os.environ.get('STORAGE_MODE', 'auto')
    LOCAL_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bucket_storage', S3_BUCKET_NAME)
    
    # Audit Database
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audit_trail.db')
    AUDIT_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audit_trail.log')

# Predefined corporate departments
DEPARTMENTS = {
    'hr': {'name': 'Human Resources', 'badge_color': 'bg-pink-100 text-pink-800 border-pink-200', 'icon': 'users'},
    'it': {'name': 'Information Technology', 'badge_color': 'bg-blue-100 text-blue-800 border-blue-200', 'icon': 'cpu'},
    'sales': {'name': 'Sales & Commercial', 'badge_color': 'bg-emerald-100 text-emerald-800 border-emerald-200', 'icon': 'trending-up'},
    'shared': {'name': 'Company-Wide Knowledge', 'badge_color': 'bg-amber-100 text-amber-800 border-amber-200', 'icon': 'globe'}
}

# Standard enterprise directory roles
USERS = {
    'hr_lead': {
        'username': 'hr_lead',
        'password': '*',
        'full_name': 'HR Operations Lead',
        'title': 'Director of Human Resources',
        'department': 'hr',
        'role': 'department_lead'
    },
    'hr_user': {
        'username': 'hr_user',
        'password': '*',
        'full_name': 'HR Specialist',
        'title': 'HR Operations Member',
        'department': 'hr',
        'role': 'department_member'
    },
    'it_admin': {
        'username': 'it_admin',
        'password': '*',
        'full_name': 'IT Security Engineer',
        'title': 'Cloud & Infrastructure Lead',
        'department': 'it',
        'role': 'department_lead'
    },
    'it_specialist': {
        'username': 'it_specialist',
        'password': '*',
        'full_name': 'IT Systems Administrator',
        'title': 'IT Infrastructure Member',
        'department': 'it',
        'role': 'department_member'
    },
    'sales_exec': {
        'username': 'sales_exec',
        'password': '*',
        'full_name': 'Sales Director',
        'title': 'Enterprise Commercial Lead',
        'department': 'sales',
        'role': 'department_lead'
    },
    'sales_rep': {
        'username': 'sales_rep',
        'password': '*',
        'full_name': 'Account Executive',
        'title': 'Sales & Commercial Member',
        'department': 'sales',
        'role': 'department_member'
    },
    'auditor': {
        'username': 'auditor',
        'password': '*',
        'full_name': 'Compliance Auditor',
        'title': 'Internal Security & Compliance',
        'department': 'compliance',
        'role': 'auditor'
    },
    'admin': {
        'username': 'admin',
        'password': '*',
        'full_name': 'Enterprise Administrator',
        'title': 'Cloud Infrastructure Administrator',
        'department': 'admin',
        'role': 'superadmin'
    }
}

# Fine-Grained Access Control Matrix Definition
def can_access_folder(user, target_dept, action='read'):
    """
    Evaluates fine-grained access control permissions.
    Returns: (allowed: bool, reason: str)
    """
    if not user:
        return False, "Unauthenticated session"
        
    role = user.get('role')
    user_dept = user.get('department')
    
    # Superadmin has full access
    if role == 'superadmin':
        return True, "Authorized by Administrator privileges"
        
    # Auditor has read-only access to all department documents for compliance verification
    if role == 'auditor':
        if action in ['read', 'search']:
            return True, "Authorized compliance read-only audit inspection"
        else:
            return False, "Auditor role has strictly read-only permissions"
            
    # Shared knowledge folder is accessible for read and write by all authenticated corporate users
    if target_dept == 'shared':
        return True, "Shared company-wide folder is accessible to all verified employees"
        
    # Department members can access their own department folder
    if user_dept == target_dept:
        return True, f"Authorized access to {target_dept.upper()} departmental storage"
        
    # Cross-department access is strictly prohibited
    return False, f"Access Denied: User in department '{user_dept.upper()}' cannot access '{target_dept.upper()}' folder (Principle of Least Privilege violated)"

def can_view_audit_trail(user):
    """Checks if the user can inspect the security audit trail"""
    if not user:
        return False
    return user.get('role') in ['superadmin', 'auditor']
