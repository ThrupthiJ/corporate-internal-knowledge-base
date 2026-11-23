import os
import sqlite3
import json
from datetime import datetime, timezone
from config import Config

def init_audit_db():
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id TEXT NOT NULL,
            user_department TEXT NOT NULL,
            user_role TEXT NOT NULL,
            action TEXT NOT NULL,
            target_dept TEXT NOT NULL,
            resource_name TEXT,
            status TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            details TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status)')
    conn.commit()
    conn.close()

def log_event(user, action, target_dept, resource_name=None, status="SUCCESS", client_ip="127.0.0.1", details=None):
    """
    Appends an immutable audit event to both SQLite DB and the append-only log file.
    """
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')
    user_id = user.get('username', 'anonymous') if user else 'anonymous'
    user_dept = user.get('department', 'unknown') if user else 'unknown'
    user_role = user.get('role', 'unknown') if user else 'unknown'

    # 1. Write to SQLite
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs 
            (timestamp, user_id, user_department, user_role, action, target_dept, resource_name, status, client_ip, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (now_str, user_id, user_dept, user_role, action, target_dept, resource_name, status, client_ip, details))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] SQLite audit log error: {e}")

    # 2. Append to structured flat log file (AWS CloudWatch / S3 Audit format)
    log_entry = {
        "event_time": now_str,
        "event_source": "aws.ec2.knowledge_base_app",
        "user_identity": {
            "username": user_id,
            "department": user_dept,
            "role": user_role
        },
        "event_name": action,
        "request_parameters": {
            "target_department": target_dept,
            "resource": resource_name
        },
        "response_elements": {
            "status": status
        },
        "source_ip_address": client_ip,
        "security_analysis": details
    }
    
    try:
        with open(Config.AUDIT_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"[!] Flat audit log error: {e}")

def get_audit_logs(limit=100, filter_status=None, filter_user=None, filter_action=None):
    """Retrieves logs with optional security filtering"""
    init_audit_db()
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = 'SELECT * FROM audit_logs WHERE 1=1'
    params = []
    
    if filter_status:
        query += ' AND status = ?'
        params.append(filter_status)
    if filter_user:
        query += ' AND user_id = ?'
        params.append(filter_user)
    if filter_action:
        query += ' AND action = ?'
        params.append(filter_action)
        
    query += ' ORDER BY id DESC LIMIT ?'
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
