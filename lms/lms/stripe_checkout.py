# Copyright (c) 2026, FOSS United and Contributors
# See license.txt

"""Stripe Checkout for LMS payments.

The `payments` app's Stripe integration charges a card token through the
Charges API, which Stripe has retired ("Card Token usage on the Customers API
and Charges API has reached end of life"). The fix upstream is still unmerged
and assumes ERPNext-style payment requests, so LMS creates the Checkout Session
itself.

The amount always comes from the LMS Payment row that get_payment_link has
already priced (coupon and tax included), never from the request. A payment is
credited only after Stripe itself says the session was paid, and only for the
session, member and amount that LMS Payment row was created for. Both the
browser return and the webhook end up in finalize_checkout_session, and
update_payment_record makes the second of them a no-op.
"""

from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import flt, get_url

from lms.lms.utils import get_lms_route, update_payment_record

# https://docs.stripe.com/currencies#zero-decimal
ZERO_DECIMAL_CURRENCIES = {
	"BIF",
	"CLP",
	"DJF",
	"GNF",
	"JPY",
	"KMF",
	"KRW",
	"MGA",
	"PYG",
	"RWF",
	"UGX",
	"VND",
	"VUV",
	"XAF",
	"XOF",
	"XPF",
}

PAID_EVENTS = ("checkout.session.completed", "checkout.session.async_payment_succeeded")

# Cards only for now. Anything else a Stripe account has switched on in the
# dashboard (wallets, bank debits) would otherwise show up on the hosted page.
PAYMENT_METHOD_TYPES = ["card"]


def is_stripe_gateway(payment_gateway: str | None) -> bool:
	if not payment_gateway:
		return False
	return frappe.db.get_value("Payment Gateway", payment_gateway, "gateway_settings") == "Stripe Settings"


def get_stripe_client(payment_gateway: str | None = None):
	import stripe

	payment_gateway = payment_gateway or frappe.db.get_single_value("LMS Settings", "payment_gateway")
	settings_name = frappe.db.get_value("Payment Gateway", payment_gateway, "gateway_controller")
	settings = frappe.get_doc("Stripe Settings", settings_name)

	return stripe.StripeClient(
		settings.get_password("secret_key", raise_exception=False),
		http_client=stripe.http_client.RequestsClient(),
	)


def to_minor_units(amount: float, currency: str) -> int:
	if (currency or "").upper() in ZERO_DECIMAL_CURRENCIES:
		return int(round(flt(amount)))
	return int(round(flt(amount) * 100))


def get_payable(payment: dict) -> float:
	"""What the learner was quoted: the total with tax when there is tax."""
	return flt(payment.amount_with_gst) or flt(payment.amount)


def create_checkout_session(
	payment_gateway: str,
	payment_name: str,
	title: str,
	description: str,
	payer_email: str,
	cancel_to: str,
) -> str:
	"""Create a hosted Checkout Session for an LMS Payment and return its URL."""
	payment = frappe.db.get_value(
		"LMS Payment", payment_name, ["name", "member", "amount", "amount_with_gst", "currency"], as_dict=True
	)
	total = get_payable(payment)
	client = get_stripe_client(payment_gateway)

	session = client.checkout.sessions.create(
		{
			"mode": "payment",
			"payment_method_types": PAYMENT_METHOD_TYPES,
			"line_items": [
				{
					"price_data": {
						"currency": payment.currency.lower(),
						"unit_amount": to_minor_units(total, payment.currency),
						"product_data": {"name": title, "description": description},
					},
					"quantity": 1,
				}
			],
			# {CHECKOUT_SESSION_ID} is Stripe's own placeholder; quoting it would break it.
			"success_url": get_url("/api/method/lms.lms.stripe_checkout.checkout_return")
			+ "?session_id={CHECKOUT_SESSION_ID}",
			"cancel_url": get_url(cancel_to),
			"customer_email": payer_email,
			"client_reference_id": payment.name,
			"metadata": {"lms_payment": payment.name},
			"payment_intent_data": {"metadata": {"lms_payment": payment.name}},
		},
		{"idempotency_key": f"lms-payment-{payment.name}"},
	)

	# The session id is what finalize_checkout_session ties the money back to.
	frappe.db.set_value("LMS Payment", payment.name, "order_id", session.id)
	return session.url


def finalize_checkout_session(session) -> dict | None:
	"""Credit the LMS Payment a paid Checkout Session belongs to.

	Returns the LMS Payment row when the session is valid and paid, otherwise
	None. Safe to call any number of times for the same session. Must run as the
	paying member, since enrolling uses the session user."""
	metadata = session.get("metadata") or {}
	payment_name = metadata.get("lms_payment")
	if not payment_name:
		return None

	payment = frappe.db.get_value(
		"LMS Payment",
		payment_name,
		[
			"name",
			"member",
			"amount",
			"amount_with_gst",
			"currency",
			"order_id",
			"payment_received",
			"payment_for_document_type",
			"payment_for_document",
		],
		as_dict=True,
	)

	# A session minted for another payment (or by anyone else) must not credit this one.
	if not payment or not payment.order_id or payment.order_id != session.get("id"):
		return None

	if session.get("payment_status") != "paid":
		return None

	if (
		session.get("amount_total") != to_minor_units(get_payable(payment), payment.currency)
		or (session.get("currency") or "").lower() != payment.currency.lower()
	):
		frappe.log_error(
			title="Stripe session amount does not match the LMS Payment",
			message=f"LMS Payment {payment.name}: quoted {get_payable(payment)} {payment.currency}, "
			f"Stripe session {session.get('id')} charged {session.get('amount_total')} "
			f"{session.get('currency')} (minor units).",
		)
		return None

	if payment.payment_received:
		return payment

	frappe.flags.data = frappe._dict(
		payment=payment.name,
		payment_gateway="Stripe",
		# The unique payment id: a replayed callback for this charge is turned away on it.
		stripe_token_id=session.get("payment_intent") or session.get("id"),
		order_id=session.get("id"),
	)
	update_payment_record(payment.payment_for_document_type, payment.payment_for_document)
	return payment


def get_destination(payment: dict, paid: bool) -> str:
	from lms.lms.payments import get_redirect_url

	certificate = frappe.db.get_value("LMS Payment", payment.name, "payment_for_certificate")
	target = get_redirect_url(payment.payment_for_document_type, payment.payment_for_document, certificate)
	if paid:
		return get_url(target)
	return get_url(f"payment-failed?redirect_to={quote(target, safe='')}")


@frappe.whitelist(methods=["GET"])
def checkout_return(session_id: str):
	"""Where Stripe sends the learner after paying. Confirms with Stripe directly
	instead of trusting the URL, then sends them on."""
	session = get_stripe_client().checkout.sessions.retrieve(session_id)
	payment_name = (session.get("metadata") or {}).get("lms_payment")
	owner = payment_name and frappe.db.get_value("LMS Payment", payment_name, "member")

	if not owner or owner != frappe.session.user:
		frappe.throw(_("This payment does not belong to you."), frappe.PermissionError)

	finalize_checkout_session(session)
	# Stripe sends the learner back with a GET, and frappe only commits the writes
	# of POST/PUT/DELETE requests: without this the enrollment is rolled back the
	# moment the redirect is sent, after the learner has paid.
	# nosemgrep: frappe-manual-commit, whitelisted-side-effect-on-get - a GET is never committed by frappe, and this write is idempotent and Stripe-verified (see above).
	frappe.db.commit()

	payment = frappe.db.get_value(
		"LMS Payment",
		payment_name,
		["name", "payment_received", "payment_for_document_type", "payment_for_document"],
		as_dict=True,
	)
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = get_destination(payment, paid=bool(payment.payment_received))


# nosemgrep: guest-whitelisted-method - Stripe's servers are not logged in; the request is authenticated by the HMAC signature of the raw body against the signing secret, and anything unsigned is rejected before any data is read. Registered in tests/guest_endpoints.txt.
@frappe.whitelist(allow_guest=True, methods=["POST"])
def stripe_webhook():
	"""Stripe's server-to-server confirmation, so a learner who closes the tab
	after paying is still enrolled. Authenticated by Stripe's signature alone."""
	import stripe

	secret = frappe.get_single("LMS Settings").get_password("stripe_webhook_secret", raise_exception=False)

	if not secret:
		frappe.local.response["http_status_code"] = 503
		return "Stripe webhook secret is not configured"

	try:
		event = stripe.Webhook.construct_event(
			frappe.request.get_data(), frappe.get_request_header("Stripe-Signature") or "", secret
		)
	except (ValueError, stripe.SignatureVerificationError):
		frappe.local.response["http_status_code"] = 400
		return "Invalid signature"

	if event["type"] not in PAID_EVENTS:
		return "Ignored"

	session = event["data"]["object"]
	payment_name = (session.get("metadata") or {}).get("lms_payment")
	member = payment_name and frappe.db.get_value("LMS Payment", payment_name, "member")

	if not member:
		return "Unknown payment"

	# nosemgrep: frappe-setuser - enrolling acts on frappe.session.user, and the webhook has no session. It acts as the member the verified payment belongs to, never a privileged user, and is reset below.
	frappe.set_user(member)
	try:
		finalize_checkout_session(session)
	finally:
		frappe.set_user("Guest")  # nosemgrep: frappe-setuser - restoring the webhook's own guest session

	return "OK"
