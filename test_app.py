import unittest
from app import app
from config import USERS

class KnowledgeBaseSecurityTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_01_unauthenticated_redirect(self):
        """Unauthenticated access should redirect to login"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_02_hr_user_access_hr_doc_allowed(self):
        """HR user accessing HR document must be ALLOWED (200 OK)"""
        with self.client.session_transaction() as sess:
            sess['username'] = 'hr_lead'
        response = self.client.get('/view/hr/HR_Employee_Handbook_2026.txt')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Employee Handbook', response.data)

    def test_03_hr_user_access_it_doc_blocked(self):
        """HR user accessing IT document must be BLOCKED (403 Forbidden)"""
        with self.client.session_transaction() as sess:
            sess['username'] = 'hr_lead'
        response = self.client.get('/view/it/Cloud_Infrastructure_Security_Manual.txt')
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'403 Forbidden', response.data)
        self.assertIn(b'Principle of Least Privilege', response.data)

    def test_04_sales_user_access_shared_doc_allowed(self):
        """Sales user accessing Shared document must be ALLOWED (200 OK)"""
        with self.client.session_transaction() as sess:
            sess['username'] = 'sales_exec'
        response = self.client.get('/view/shared/Corporate_Code_of_Conduct.txt')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Corporate Code of Business Conduct', response.data)

    def test_05_auditor_cross_dept_read_allowed(self):
        """Auditor has compliance read-only access to IT document"""
        with self.client.session_transaction() as sess:
            sess['username'] = 'auditor'
        response = self.client.get('/view/it/Incident_Response_Playbook.txt')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Incident Response Playbook', response.data)

    def test_06_audit_trail_view(self):
        """Superadmin or Auditor can view audit logs"""
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
        response = self.client.get('/audit')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Security Audit Trail', response.data)

if __name__ == '__main__':
    unittest.main()
