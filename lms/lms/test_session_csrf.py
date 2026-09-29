import frappe
from frappe.tests import UnitTestCase

from lms.lms.user import on_session_creation


class TestCsrfTokenAtSessionCreation(UnitTestCase):
	def setUp(self):
		self._session = frappe.local.session
		frappe.local.session = frappe._dict(user="Administrator", data=frappe._dict())

	def tearDown(self):
		frappe.local.session = self._session

	def test_hook_is_registered(self):
		self.assertIn("lms.lms.user.on_session_creation", frappe.get_hooks("on_session_creation"))

	def test_mints_token_for_new_session(self):
		on_session_creation(login_manager=None)
		self.assertTrue(frappe.local.session.data.csrf_token)

	def test_keeps_existing_token(self):
		frappe.local.session.data.csrf_token = "existing-token"
		on_session_creation(login_manager=None)
		self.assertEqual(frappe.local.session.data.csrf_token, "existing-token")
