# Copyright (c) 2026, FOSS United and Contributors
# See license.txt

"""What a learner is told after paying for a course they cannot be enrolled in yet.

Frappe's own error page hides the reason behind "Uncaught Exception", so these
are shown on its message page instead."""

import frappe
from frappe import _
from frappe.utils import escape_html, get_url
from frappe.utils.response import redirect_to_message


def message_url(title: str, html: str, indicator_color: str = "green") -> str:
	"""Store a message for Frappe's /message page and return its address.

	redirect_to_message answers a plain request by setting a redirect on the
	response and an ajax one by returning the address, and this is called from
	both, so take the address in either case and leave the response alone."""
	location = redirect_to_message(title, html, indicator_color=indicator_color)

	if location is None:
		location = frappe.local.response.pop("location")
		frappe.local.response.pop("type", None)

	return get_url(location)


def preregistered(course: str) -> str:
	return message_url(
		_("You are pre-registered"),
		_(
			"Thank you. We have received your payment for {0}, and you are pre-registered.<br><br>"
			"This course has not started yet. Please wait for it to start; we will set up your access."
		).format(f"<b>{escape_html(get_course_title(course))}</b>"),
	)


def payment_received_enrolment_pending(course: str) -> str:
	return message_url(
		_("We have received your payment"),
		_(
			"Thank you. Your payment for {0} went through, but we could not open your access automatically.<br><br>"
			"Your payment is safe, and an administrator will finish setting up your access."
		).format(f"<b>{escape_html(get_course_title(course))}</b>"),
		indicator_color="orange",
	)


def get_course_title(course: str) -> str:
	return frappe.db.get_value("LMS Course", course, "title") or course
