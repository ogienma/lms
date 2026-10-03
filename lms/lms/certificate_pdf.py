# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

"""The certificate as a tagged PDF.

Frappe's own download_pdf renders with wkhtmltopdf, which writes an untagged PDF with no
document language or title: a screen reader gets nothing to navigate. Frappe's Chrome
generator can tag the PDF, but nothing turns that option on, so the certificate goes
through this module instead. Where Chromium is not available, the old untagged PDF is
served rather than none.
"""

import re
from html import escape

import frappe
from frappe import _
from frappe.utils.print_format import validate_print_permission

TAGGED_PDF_OPTIONS = {"generate-tagged-pdf": True}


@frappe.whitelist(allow_guest=True)
@frappe.concurrent_limit()
def download_certificate(name: str):
	"""Same access as frappe.utils.print_format.download_pdf, which the certificate links used."""
	doc = frappe.get_doc("LMS Certificate", name)
	validate_print_permission(doc)

	frappe.local.response.filename = f"{name.replace(' ', '-').replace('/', '-')}.pdf"
	frappe.local.response.filecontent = render_certificate_pdf(doc)
	frappe.local.response.type = "pdf"


def render_certificate_pdf(doc) -> bytes:
	template = doc.template
	html = frappe.get_print("LMS Certificate", doc.name, template, doc=doc, as_pdf=False, no_letterhead=1)

	try:
		pdf = _tagged_pdf(template, _with_title(html, doc))
	except Exception:
		frappe.log_error(title="Tagged certificate PDF failed; serving the untagged one")
		pdf = None

	return pdf or frappe.get_print(
		"LMS Certificate", doc.name, template, doc=doc, as_pdf=True, no_letterhead=1
	)


def _tagged_pdf(template: str, html: str) -> bytes | None:
	from frappe.utils.pdf import get_chrome_pdf

	return get_chrome_pdf(template, html, dict(TAGGED_PDF_OPTIONS), None, "chrome")


def _with_title(html: str, doc) -> str:
	"""The PDF's title comes from <title>, which Frappe fills with the document title: the
	learner's name. A reader announces the title first, so name what the document is."""
	course = frappe.db.get_value("LMS Course", doc.course, "title") if doc.course else None
	title = _("Certificate of Completion")
	if course:
		title = f"{title} - {course}"
	tag = f"<title>{escape(title)}</title>"
	html, replaced = re.subn(r"<title>.*?</title>", lambda _match: tag, html, count=1, flags=re.S)
	return html if replaced else html.replace("<head>", f"<head>{tag}", 1)
