# Frappe's login context, unchanged: lms/www/login.html only differs from Frappe's template
# in markup (see its header). The whitelisted login helpers stay in frappe.www.login.
from frappe.www.login import get_context as frappe_get_context

no_cache = True


def get_context(context):
	return frappe_get_context(context)
