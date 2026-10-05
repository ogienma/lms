from urllib.parse import quote

import frappe


def get_context(context):
	context.no_cache = 1
	certificate_id = frappe.form_dict.certificate_id

	frappe.local.flags.redirect_location = (
		f"/api/method/lms.lms.certificate_pdf.download_certificate?name={quote(certificate_id, safe='')}"
	)
	raise frappe.Redirect
