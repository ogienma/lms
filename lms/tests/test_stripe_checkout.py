# Copyright (c) 2026, FOSS United and Contributors
# See license.txt

import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import frappe

from lms.lms import stripe_checkout
from lms.lms.stripe_checkout import (
	checkout_return,
	create_checkout_session,
	finalize_checkout_session,
	stripe_webhook,
	to_minor_units,
)
from lms.lms.test_helpers import BaseTestUtils

WEBHOOK_SECRET = "whsec_unit_test_secret"


class TestStripeCheckout(BaseTestUtils):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		hash = frappe.generate_hash(length=6)
		cls.instructor = cls._create_user(
			f"sinstr-{hash}@example.com", "Sam", "Instr", ["Course Creator", "Moderator"]
		)
		cls.learner = cls._create_user(f"slearn-{hash}@example.com", "Lee", "Learner", ["LMS Student"])
		cls.other_learner = cls._create_user(f"sother-{hash}@example.com", "Oz", "Other", ["LMS Student"])

	def setUp(self):
		super().setUp()
		self.course = self._create_course(
			title=f"Stripe Course {frappe.generate_hash(length=6)}", instructor=self.instructor.email
		)
		self.course.db_set({"paid_course": 1, "course_price": 5, "currency": "USD"})
		frappe.set_user(self.learner.email)
		# checkout_return commits (Stripe redirects with a GET, which frappe does not
		# commit). A real commit here would persist the fixtures and discard the
		# savepoint that BaseTestUtils rolls back to.
		commit = patch.object(frappe.db, "commit")
		self.commit = commit.start()
		self.addCleanup(commit.stop)

	def _payment(self, amount=5, amount_with_gst=0, order_id=None):
		address = frappe.new_doc("Address")
		address.update(
			{
				"address_title": f"Stripe Tester {frappe.generate_hash(length=8)}",
				"address_type": "Billing",
				"address_line1": "1 Test Street",
				"city": "Austin",
				"country": "United States",
				"email_id": frappe.session.user,
			}
		)
		# nosemgrep: lms-unjustified-ignore-permissions - test fixture
		address.save(ignore_permissions=True)
		# nosemgrep: lms-unjustified-ignore-permissions - test fixture
		frappe.get_doc({"doctype": "LMS Source", "source": "Website"}).insert(
			ignore_permissions=True, ignore_if_duplicate=True
		)

		payment = frappe.new_doc("LMS Payment")
		payment.update(
			{
				"member": frappe.session.user,
				"billing_name": "Stripe Tester",
				"address": address.name,
				"source": "Website",
				"amount": amount,
				"amount_with_gst": amount_with_gst,
				"currency": "USD",
				"payment_for_document_type": "LMS Course",
				"payment_for_document": self.course.name,
				"order_id": order_id,
			}
		)
		# nosemgrep: lms-unjustified-ignore-permissions - test fixture
		payment.save(ignore_permissions=True)
		return payment

	def _session(self, payment, **overrides):
		session = {
			"id": "cs_test_123",
			"payment_status": "paid",
			"amount_total": 500,
			"currency": "usd",
			"payment_intent": "pi_test_123",
			"metadata": {"lms_payment": payment.name},
		}
		session.update(overrides)
		return session

	def _is_enrolled(self, member=None):
		return bool(
			frappe.db.exists(
				"LMS Enrollment", {"member": member or self.learner.email, "course": self.course.name}
			)
		)

	# Creating the session

	def test_minor_units(self):
		self.assertEqual(to_minor_units(5, "USD"), 500)
		self.assertEqual(to_minor_units(19.99, "USD"), 1999)
		self.assertEqual(to_minor_units(1000, "JPY"), 1000)

	def test_session_uses_the_lms_payment_amount_and_only_cards(self):
		payment = self._payment(amount=5, amount_with_gst=5.4)
		client = MagicMock()
		client.checkout.sessions.create.return_value = SimpleNamespace(
			id="cs_test_123", url="https://checkout.stripe.com/c/pay/cs_test_123"
		)

		with patch.object(stripe_checkout, "get_stripe_client", return_value=client):
			url = create_checkout_session(
				"Stripe-x", payment.name, "Course", "Billing for course", self.learner.email, "/lms/courses/x"
			)

		params, options = client.checkout.sessions.create.call_args.args
		self.assertEqual(url, "https://checkout.stripe.com/c/pay/cs_test_123")
		self.assertEqual(params["line_items"][0]["price_data"]["unit_amount"], 540)
		self.assertEqual(params["line_items"][0]["price_data"]["currency"], "usd")
		self.assertEqual(params["payment_method_types"], ["card"])
		self.assertEqual(params["metadata"], {"lms_payment": payment.name})
		self.assertEqual(options["idempotency_key"], f"lms-payment-{payment.name}")
		# Stripe fills this placeholder in, so it must reach it unescaped.
		self.assertTrue(params["success_url"].endswith("?session_id={CHECKOUT_SESSION_ID}"))
		self.assertEqual(frappe.db.get_value("LMS Payment", payment.name, "order_id"), "cs_test_123")

	# Crediting a payment

	def test_paid_session_enrolls_and_records_the_payment(self):
		payment = self._payment(order_id="cs_test_123")

		finalize_checkout_session(self._session(payment))

		self.assertTrue(frappe.db.get_value("LMS Payment", payment.name, "payment_received"))
		self.assertEqual(frappe.db.get_value("LMS Payment", payment.name, "payment_id"), "pi_test_123")
		self.assertTrue(self._is_enrolled())

	def test_second_delivery_of_the_same_session_changes_nothing(self):
		payment = self._payment(order_id="cs_test_123")

		finalize_checkout_session(self._session(payment))
		finalize_checkout_session(self._session(payment))

		self.assertEqual(
			frappe.db.count("LMS Enrollment", {"member": self.learner.email, "course": self.course.name}), 1
		)

	def test_unpaid_session_is_not_credited(self):
		payment = self._payment(order_id="cs_test_123")

		self.assertIsNone(finalize_checkout_session(self._session(payment, payment_status="unpaid")))

		self.assertFalse(frappe.db.get_value("LMS Payment", payment.name, "payment_received"))
		self.assertFalse(self._is_enrolled())

	def test_session_for_a_different_checkout_is_not_credited(self):
		payment = self._payment(order_id="cs_test_123")

		self.assertIsNone(finalize_checkout_session(self._session(payment, id="cs_test_other")))

		self.assertFalse(self._is_enrolled())

	def test_underpaid_session_is_not_credited(self):
		payment = self._payment(order_id="cs_test_123")

		self.assertIsNone(finalize_checkout_session(self._session(payment, amount_total=1)))

		self.assertFalse(self._is_enrolled())

	def test_wrong_currency_is_not_credited(self):
		payment = self._payment(order_id="cs_test_123")

		self.assertIsNone(finalize_checkout_session(self._session(payment, currency="eur")))

		self.assertFalse(self._is_enrolled())

	def test_session_without_our_metadata_is_ignored(self):
		self.assertIsNone(finalize_checkout_session({"id": "cs_x", "payment_status": "paid", "metadata": {}}))

	# Browser return

	def test_return_refuses_someone_elses_payment(self):
		payment = self._payment(order_id="cs_test_123")
		client = MagicMock()
		client.checkout.sessions.retrieve.return_value = self._session(payment)
		frappe.set_user(self.other_learner.email)

		with patch.object(stripe_checkout, "get_stripe_client", return_value=client):
			with self.assertRaises(frappe.PermissionError):
				checkout_return("cs_test_123")

		self.assertFalse(self._is_enrolled(self.other_learner.email))

	def test_return_credits_the_owner_and_redirects_to_the_course(self):
		payment = self._payment(order_id="cs_test_123")
		client = MagicMock()
		client.checkout.sessions.retrieve.return_value = self._session(payment)

		with patch.object(stripe_checkout, "get_stripe_client", return_value=client):
			checkout_return("cs_test_123")

		self.assertEqual(frappe.local.response["type"], "redirect")
		self.assertTrue(frappe.local.response["location"].endswith(f"/courses/{self.course.name}"))
		self.assertTrue(self._is_enrolled())

	def test_return_commits_because_stripe_redirects_with_a_get(self):
		payment = self._payment(order_id="cs_test_123")
		client = MagicMock()
		client.checkout.sessions.retrieve.return_value = self._session(payment)

		with patch.object(stripe_checkout, "get_stripe_client", return_value=client):
			checkout_return("cs_test_123")

		self.commit.assert_called_once()

	def test_return_for_an_unpaid_session_goes_to_the_failure_page(self):
		payment = self._payment(order_id="cs_test_123")
		client = MagicMock()
		client.checkout.sessions.retrieve.return_value = self._session(payment, payment_status="unpaid")

		with patch.object(stripe_checkout, "get_stripe_client", return_value=client):
			checkout_return("cs_test_123")

		self.assertIn("payment-failed", frappe.local.response["location"])
		self.assertFalse(self._is_enrolled())

	# Webhook

	def _post_webhook(self, payload: dict, secret=WEBHOOK_SECRET, sign=True, header=None):
		body = json.dumps(payload).encode()
		timestamp = int(time.time())
		signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
		header = header if header is not None else f"t={timestamp},v1={signature}" if sign else "t=1,v1=bad"

		settings = SimpleNamespace(get_password=lambda *a, **k: WEBHOOK_SECRET)
		request = SimpleNamespace(get_data=lambda: body)
		with (
			patch.object(frappe, "request", request, create=True),
			patch.object(frappe, "get_request_header", return_value=header),
			patch.object(frappe, "get_single", return_value=settings),
		):
			frappe.local.response = frappe._dict()
			result = stripe_webhook()
		return result, frappe.local.response.get("http_status_code")

	def _event(self, session, type="checkout.session.completed"):
		return {
			"id": "evt_1",
			"object": "event",
			"api_version": "2024-06-20",
			"type": type,
			"data": {"object": {"object": "checkout.session", **session}},
		}

	def test_webhook_with_a_bad_signature_is_rejected(self):
		payment = self._payment(order_id="cs_test_123")

		result, status = self._post_webhook(self._event(self._session(payment)), sign=False)

		self.assertEqual(status, 400)
		self.assertFalse(self._is_enrolled())

	def test_webhook_signed_with_another_secret_is_rejected(self):
		payment = self._payment(order_id="cs_test_123")

		_, status = self._post_webhook(self._event(self._session(payment)), secret="whsec_attacker")

		self.assertEqual(status, 400)
		self.assertFalse(self._is_enrolled())

	def test_signed_webhook_enrolls_the_member_without_a_browser(self):
		payment = self._payment(order_id="cs_test_123")
		frappe.set_user("Guest")

		result, status = self._post_webhook(self._event(self._session(payment)))

		self.assertEqual(result, "OK")
		self.assertIsNone(status)
		self.assertTrue(frappe.db.get_value("LMS Payment", payment.name, "payment_received"))
		self.assertTrue(self._is_enrolled())

	def test_webhook_after_the_browser_return_does_not_double_enroll(self):
		payment = self._payment(order_id="cs_test_123")
		finalize_checkout_session(self._session(payment))

		self._post_webhook(self._event(self._session(payment)))

		self.assertEqual(
			frappe.db.count("LMS Enrollment", {"member": self.learner.email, "course": self.course.name}), 1
		)

	def test_other_events_are_ignored(self):
		payment = self._payment(order_id="cs_test_123")

		result, _ = self._post_webhook(self._event(self._session(payment), type="charge.refunded"))

		self.assertEqual(result, "Ignored")
		self.assertFalse(self._is_enrolled())

	def test_webhook_refuses_when_no_secret_is_configured(self):
		settings = SimpleNamespace(get_password=lambda *a, **k: None)
		with (
			patch.object(frappe, "request", SimpleNamespace(get_data=lambda: b"{}"), create=True),
			patch.object(frappe, "get_single", return_value=settings),
		):
			frappe.local.response = frappe._dict()
			stripe_webhook()

		self.assertEqual(frappe.local.response["http_status_code"], 503)
