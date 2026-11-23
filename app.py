import os
import io
import csv
from datetime import datetime, timezone
from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, flash, send_file, jsonify, abort
)
from config import Config, DEPARTMENTS, USERS, can_access_folder, can_view_audit_trail
from storage import get_storage
from audit import init_audit_db, log_event, get_audit_logs

app = Flask(__name__)
app.config.from_object(Config)

# Initialize storage and audit DB on startup
storage, storage_engine_name = get_storage()
init_audit_db()

def get_current_user():
    username = session.get('username')
    if username and username in USERS:
        return USERS[username]
    return None

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

@app.context_processor
def inject_global_context():
    user = get_current_user()
    return {
        'current_user': user,
        'departments': DEPARTMENTS,
        'users_list': USERS,
        'storage_engine_name': storage_engine_name,
        's3_bucket_name': Config.S3_BUCKET_NAME,
        'can_view_audit': can_view_audit_trail(user)
    }

# ----------------------------------------------------------------------
# Authentication Routes
# ----------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        raw_username = request.form.get('username', '').strip()
        username = raw_username.lower() if raw_username else 'admin'
        
        user = USERS.get(username)
        if not user:
            # Dynamically resolve department based on username or grant admin access
            if 'hr' in username:
                dept, role, title = 'hr', 'department_member', 'HR Specialist'
            elif 'it' in username or 'tech' in username:
                dept, role, title = 'it', 'department_member', 'IT Systems Engineer'
            elif 'sale' in username:
                dept, role, title = 'sales', 'department_member', 'Account Executive'
            elif 'audit' in username:
                dept, role, title = 'compliance', 'auditor', 'Compliance Auditor'
            else:
                dept, role, title = 'admin', 'superadmin', 'Enterprise Administrator'

            user = {
                'username': raw_username or 'admin',
                'password': '*',
                'full_name': raw_username.capitalize() if raw_username else 'Enterprise User',
                'title': title,
                'department': dept,
                'role': role
            }
            USERS[username] = user
            USERS[raw_username] = user

        session['username'] = user['username']
        log_event(
            user=user,
            action='LOGIN',
            target_dept='system',
            resource_name='SessionAuth',
            status='SUCCESS',
            client_ip=get_client_ip(),
            details=f"User {user['full_name']} ({user['department'].upper()}) authenticated successfully."
        )
        flash(f"Welcome back, {user['full_name']}!", 'success')
        return redirect(url_for('index'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    user = get_current_user()
    if user:
        log_event(
            user=user,
            action='LOGOUT',
            target_dept='system',
            resource_name='SessionAuth',
            status='SUCCESS',
            client_ip=get_client_ip(),
            details=f"User {user['username']} logged out cleanly."
        )
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/switch-user/<username>')
def switch_user(username):
    """Quick-switch route for presentation and demonstration"""
    if username in USERS:
        session['username'] = username
        user = USERS[username]
        log_event(
            user=user,
            action='ROLE_SWITCH',
            target_dept='system',
            resource_name='DemoRolePicker',
            status='SUCCESS',
            client_ip=get_client_ip(),
            details=f"Switched active demo session to {user['full_name']} ({user['role']})."
        )
        flash(f"Switched role to {user['full_name']} ({user['title']})", 'success')
    return redirect(request.referrer or url_for('index'))

# ----------------------------------------------------------------------
# Main Document Management & Knowledge Base Routes
# ----------------------------------------------------------------------
@app.route('/')
def index():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    selected_dept = request.args.get('dept', 'all')
    search_query = request.args.get('q', '').strip().lower()
    
    # Fetch all files from storage
    all_files = storage.list_files()
    filtered_files = []
    
    for f in all_files:
        f_dept = f['department']
        
        # Check if user has permission to see this document in index/search
        allowed, _ = can_access_folder(user, f_dept, 'read')
        f['is_accessible'] = allowed
        
        # Apply department filter tab
        if selected_dept != 'all' and f_dept != selected_dept:
            continue
            
        # Apply search query
        if search_query:
            if search_query not in f['filename'].lower() and search_query not in f_dept.lower():
                continue
                
        filtered_files.append(f)
        
    if search_query:
        log_event(
            user=user,
            action='SEARCH_DOCUMENTS',
            target_dept=selected_dept,
            resource_name=search_query,
            status='SUCCESS',
            client_ip=get_client_ip(),
            details=f"Search performed for '{search_query}'. Returned {len(filtered_files)} matches."
        )

    return render_template(
        'index.html',
        files=filtered_files,
        selected_dept=selected_dept,
        search_query=search_query
    )

@app.route('/view/<dept>/<filename>')
def view_document(dept, filename):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    allowed, reason = can_access_folder(user, dept, 'read')
    
    if not allowed:
        # Security Task 4: Audit trail for unauthorized attempts
        log_event(
            user=user,
            action='UNAUTHORIZED_ACCESS_ATTEMPT',
            target_dept=dept,
            resource_name=filename,
            status='BLOCKED_403',
            client_ip=get_client_ip(),
            details=f"SECURITY ALERT: {reason}. User attempted unauthorized read on restricted file '{filename}'."
        )
        return render_template('access_denied.html', 
                               dept=dept, 
                               filename=filename, 
                               reason=reason), 403

    # Access permitted
    file_bytes, content_type = storage.get_file(dept, filename)
    if not file_bytes:
        flash("Document not found in storage.", "error")
        return redirect(url_for('index'))
        
    log_event(
        user=user,
        action='VIEW_DOCUMENT',
        target_dept=dept,
        resource_name=filename,
        status='SUCCESS',
        client_ip=get_client_ip(),
        details=f"Authorized document inspection for '{filename}'."
    )
    
    # Check if text file to display inline
    try:
        content_text = file_bytes.decode('utf-8')
        is_text = True
    except UnicodeDecodeError:
        content_text = "[Binary Content - Please download to view]"
        is_text = False
        
    return render_template('view_doc.html', 
                           dept=dept, 
                           filename=filename, 
                           content=content_text, 
                           is_text=is_text)

@app.route('/download/<dept>/<filename>')
def download_document(dept, filename):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    allowed, reason = can_access_folder(user, dept, 'read')
    
    if not allowed:
        log_event(
            user=user,
            action='UNAUTHORIZED_DOWNLOAD_ATTEMPT',
            target_dept=dept,
            resource_name=filename,
            status='BLOCKED_403',
            client_ip=get_client_ip(),
            details=f"SECURITY VIOLATION: {reason}. Direct file download blocked for '{filename}'."
        )
        return render_template('access_denied.html', dept=dept, filename=filename, reason=reason), 403

    file_bytes, content_type = storage.get_file(dept, filename)
    if not file_bytes:
        flash("File not found in storage.", "error")
        return redirect(url_for('index'))
        
    log_event(
        user=user,
        action='DOWNLOAD_DOCUMENT',
        target_dept=dept,
        resource_name=filename,
        status='SUCCESS',
        client_ip=get_client_ip(),
        details=f"Authorized download completed for '{filename}' from s3://{Config.S3_BUCKET_NAME}/{dept}/."
    )
    
    return send_file(
        io.BytesIO(file_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype=content_type
    )

@app.route('/upload', methods=['POST'])
def upload_document():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    target_dept = request.form.get('target_dept')
    uploaded_file = request.files.get('file')
    
    if not uploaded_file or uploaded_file.filename == '':
        flash("No file selected for upload.", "error")
        return redirect(url_for('index'))
        
    # Check upload permission
    allowed, reason = can_access_folder(user, target_dept, 'upload')
    if not allowed:
        log_event(
            user=user,
            action='UNAUTHORIZED_UPLOAD_ATTEMPT',
            target_dept=target_dept,
            resource_name=uploaded_file.filename,
            status='BLOCKED_403',
            client_ip=get_client_ip(),
            details=f"UPLOAD BLOCKED: {reason}. Attempted unauthorized upload to '{target_dept.upper()}' storage prefix."
        )
        flash(f"Upload Denied: {reason}", "error")
        return redirect(url_for('index'))

    # Process upload
    filename = os.path.basename(uploaded_file.filename)
    file_bytes = uploaded_file.read()
    content_type = uploaded_file.content_type or 'text/plain'
    
    storage.upload_file(target_dept, filename, file_bytes, content_type)
    
    log_event(
        user=user,
        action='UPLOAD_DOCUMENT',
        target_dept=target_dept,
        resource_name=filename,
        status='SUCCESS',
        client_ip=get_client_ip(),
        details=f"Document '{filename}' ({len(file_bytes)} bytes) successfully stored in {target_dept.upper()} folder."
    )
    
    flash(f"Document '{filename}' successfully uploaded to {target_dept.upper()} knowledge folder!", "success")
    return redirect(url_for('index', dept=target_dept))

@app.route('/delete/<dept>/<filename>', methods=['POST'])
def delete_document(dept, filename):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    allowed, reason = can_access_folder(user, dept, 'delete')
    if not allowed or user.get('role') not in ['department_lead', 'superadmin']:
        log_event(
            user=user,
            action='UNAUTHORIZED_DELETE_ATTEMPT',
            target_dept=dept,
            resource_name=filename,
            status='BLOCKED_403',
            client_ip=get_client_ip(),
            details=f"DELETE DENIED: Only department leads or administrators can delete records."
        )
        flash("Permission Denied: Only Department Leads or Administrators can delete files.", "error")
        return redirect(url_for('index', dept=dept))
        
    storage.delete_file(dept, filename)
    log_event(
        user=user,
        action='DELETE_DOCUMENT',
        target_dept=dept,
        resource_name=filename,
        status='SUCCESS',
        client_ip=get_client_ip(),
        details=f"Document '{filename}' purged from storage."
    )
    flash(f"Document '{filename}' deleted.", "info")
    return redirect(url_for('index', dept=dept))

# ----------------------------------------------------------------------
# Audit Trail & Security Monitoring Routes
# ----------------------------------------------------------------------
@app.route('/audit')
def audit_view():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
        
    filter_status = request.args.get('status')
    filter_user = request.args.get('user')
    filter_action = request.args.get('action')
    
    logs = get_audit_logs(
        limit=200,
        filter_status=filter_status,
        filter_user=filter_user,
        filter_action=filter_action
    )
    
    # Calculate quick security metrics
    total_events = len(logs)
    blocked_count = sum(1 for l in logs if 'BLOCKED' in l['status'] or '403' in l['status'])
    upload_count = sum(1 for l in logs if 'UPLOAD' in l['action'])
    download_count = sum(1 for l in logs if 'DOWNLOAD' in l['action'])
    
    return render_template(
        'audit.html',
        logs=logs,
        total_events=total_events,
        blocked_count=blocked_count,
        upload_count=upload_count,
        download_count=download_count,
        active_status=filter_status,
        active_user=filter_user,
        active_action=filter_action
    )

@app.route('/audit/export/csv')
def export_audit_csv():
    user = get_current_user()
    if not user or not can_view_audit_trail(user):
        flash("Access Denied: Only Auditors and Administrators can export audit trail logs.", "error")
        return redirect(url_for('index'))
        
    logs = get_audit_logs(limit=1000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Event ID', 'Timestamp (UTC)', 'User ID', 'Department', 'Role', 'Action', 'Target Folder', 'Resource', 'Status', 'Client IP', 'Security Context'])
    
    for log in logs:
        writer.writerow([
            log['id'],
            log['timestamp'],
            log['user_id'],
            log['user_department'],
            log['user_role'],
            log['action'],
            log['target_dept'],
            log['resource_name'],
            log['status'],
            log['client_ip'],
            log['details']
        ])
        
    output.seek(0)
    log_event(
        user=user,
        action='EXPORT_AUDIT_CSV',
        target_dept='system',
        resource_name='AuditTrailReport.csv',
        status='SUCCESS',
        client_ip=get_client_ip(),
        details="Exported full audit log history to CSV format for external compliance inspection."
    )
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"audit_trail_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    )

# ----------------------------------------------------------------------
# Architecture & Access Control Matrix Viewer
# ----------------------------------------------------------------------
@app.route('/architecture')
def architecture_view():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    return render_template('architecture.html')

if __name__ == '__main__':
    # Initialize seeds if empty
    from seed_data import seed
    seed()
    print("[*] Launching Corporate Internal Knowledge Base on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
