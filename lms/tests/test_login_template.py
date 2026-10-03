# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.website.page_renderers.template_page import TemplatePage

LMS_LOGIN = Path(frappe.get_app_path("lms", "www", "login.html"))
FRAPPE_LOGIN = Path(frappe.get_app_path("frappe", "www", "login.html"))


def _lms_template_body() -> str:
	"""lms/www/login.html without the {# ... #} header comment that explains the copy."""
	return re.sub(r"\A\{#.*?#\}\n", "", LMS_LOGIN.read_text(), count=1, flags=re.S)


def _frappe_template_with_our_edits() -> str:
	"""The two changes lms/www/login.html makes to Frappe's login page (issue #35)."""
	source = FRAPPE_LOGIN.read_text()
	source = source.replace("text-ink-gray-5", "text-ink-gray-7")
	return source.replace(
		'<img class="app-logo" src="{{ logo }}">',
		'<img class="app-logo" src="{{ logo }}" alt="{{ app_name }}">',
	)


class TestLoginTemplate(IntegrationTestCase):
	def test_the_copy_differs_from_frappes_login_only_by_our_two_edits(self):
		self.assertEqual(
			_lms_template_body(),
			_frappe_template_with_our_edits(),
			"Frappe's www/login.html has changed. Re-apply the two accessibility edits "
			"(logo alt, text-ink-gray-7) to lms/www/login.html on top of the new file, "
			"and keep its header comment.",
		)

	def test_both_edits_are_actually_present(self):
		# The comparison above passes trivially if Frappe's markup stops matching the
		# replace patterns (both sides would then be unedited). Guard that separately.
		body = _lms_template_body()
		self.assertIn('alt="{{ app_name }}"', body)
		self.assertNotIn("text-ink-gray-5", body)
		self.assertIn("text-ink-gray-7", body)

	def test_the_login_page_resolves_to_the_lms_copy(self):
		page = TemplatePage("login", 200)
		self.assertTrue(page.can_render())
		self.assertEqual(page.app, "lms")
		self.assertEqual(
			Path(frappe.get_app_path(page.app, page.template_path)).resolve(), LMS_LOGIN.resolve()
		)

	def test_the_lms_context_is_frappes(self):
		from lms.www.login import get_context

		context = frappe._dict()
		# A signed-in user is redirected away from the login page before any context is built.
		frappe.set_user("Guest")
		self.addCleanup(frappe.set_user, "Administrator")
		with patch.object(frappe.local, "request", SimpleNamespace(args={}, path="/login"), create=True):
			get_context(context)
		self.assertTrue(context.app_name)
		self.assertEqual(context.for_test, "login.html")
