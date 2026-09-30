# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import json

import frappe
from bs4 import BeautifulSoup

# EMDRIA: every image in course content carries alt text. Run from a bench console:
#   bench --site <site> execute lms.lms.image_alt_audit.audit
# An image passes with a description, or with alt="" (an author marking it decorative).
# Only an absent or blank-by-omission alt is reported.

HTML_FIELDS = (
	("LMS Course", "description"),
	("LMS Course", "short_introduction"),
	("LMS Batch", "description"),
	("LMS Quiz Question", "question"),
	("LMS Assignment", "question"),
	("LMS Programming Exercise", "problem_statement"),
	("User", "bio"),
)


def html_images_missing_alt(html: str | None) -> list[str]:
	"""src of every <img> in `html` that has no alt attribute at all."""
	if not isinstance(html, str) or "<img" not in html.lower():
		return []
	return [img.get("src", "") for img in BeautifulSoup(html, "html.parser").find_all("img") if img.get("alt") is None]


def lesson_images_missing_alt(content: str | None) -> list[str]:
	"""Image blocks in a lesson's EditorJS JSON with no alt and not marked decorative,
	plus any raw <img> inside its text blocks."""
	try:
		blocks = json.loads(content or "{}").get("blocks", [])
	except (ValueError, AttributeError):
		return []

	missing = []
	for block in blocks:
		data = block.get("data") or {}
		if block.get("type") == "image":
			# The editor saves an undescribed image as alt="" too, so only the decorative
			# flag tells "left empty" from "marked decorative".
			if not (data.get("alt") or "").strip() and not data.get("decorative"):
				missing.append(data.get("url", ""))
			continue
		for value in data.values():
			missing += html_images_missing_alt(value) if isinstance(value, str) else []
	return missing


def audit() -> list[dict]:
	"""Every stored image that lacks alt text, as {doctype, name, field, src}."""
	found = []

	for name, content in frappe.get_all("Course Lesson", fields=["name", "content"], as_list=True):
		found += [
			{"doctype": "Course Lesson", "name": name, "field": "content", "src": src}
			for src in lesson_images_missing_alt(content)
		]

	for doctype, field in HTML_FIELDS:
		if not frappe.get_meta(doctype).has_field(field):
			continue
		for name, value in frappe.get_all(doctype, fields=["name", field], as_list=True):
			found += [
				{"doctype": doctype, "name": name, "field": field, "src": src}
				for src in html_images_missing_alt(value)
			]

	return found
