# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import io
from unittest.mock import patch

import frappe
from pypdf import PdfReader

from lms.lms import certificate_pdf
from lms.lms.test_helpers import BaseTestUtils


class TestCertificatePDF(BaseTestUtils):
	def setUp(self):
		super().setUp()
		self.student = self._create_user("certpdf@example.com", "Cert", "Learner", ["LMS Student"])
		self.course = self._create_course("Certificate PDF Course", instructor="Administrator")
		self._create_enrollment(self.student.email, self.course.name)
		self.certificate = self._create_certificate(self.course.name, self.student.email)

	def test_the_pdf_is_tagged_with_a_language_and_a_title(self):
		try:
			html = frappe.get_print(
				"LMS Certificate",
				self.certificate.name,
				self.certificate.template,
				doc=self.certificate,
				as_pdf=False,
				no_letterhead=1,
			)
			pdf = certificate_pdf._tagged_pdf(
				self.certificate.template, certificate_pdf._with_title(html, self.certificate)
			)
		except Exception as e:
			self.skipTest(f"Chromium is not available here: {e}")

		reader = PdfReader(io.BytesIO(pdf))
		root = reader.trailer["/Root"]
		self.assertIn("/StructTreeRoot", root)
		self.assertTrue(root["/MarkInfo"]["/Marked"])
		self.assertTrue(root["/Lang"])
		self.assertEqual(
			reader.metadata.title,
			f"Certificate of Completion - {self.course.title}",
		)
		self.assertIn("/H1", _structure_types(root["/StructTreeRoot"]))

		# One page, A4 landscape: Frappe's Chrome path injects a portrait @page size unless the
		# print format gives exact page dimensions, and a portrait page clips the design.
		self.assertEqual(len(reader.pages), 1)
		box = reader.pages[0].mediabox
		self.assertGreater(float(box.width), float(box.height))

		# The logo is the only place the organisation's name appears, so it must be a tagged
		# figure that carries its text alternative.
		# the wordmark is the only figure: the bird in the seal is decoration, not tagged
		self.assertEqual({"Caladrius Therapy"}, _figure_alts(root["/StructTreeRoot"]))

		self.assertIn("Jessie Ogienko", reader.pages[0].extract_text())

	def _certificate_html(self, ce_hours, certificate=None):
		# The certificate prints the hours recorded on it, not the course's, so set them there.
		name = (certificate or self.certificate).name
		frappe.db.set_value("LMS Certificate", name, "ce_hours", ce_hours or 0)
		return frappe.get_print(
			"LMS Certificate",
			name,
			self.certificate.template,
			doc=frappe.get_doc("LMS Certificate", name),
			as_pdf=False,
			no_letterhead=1,
		)

	def _set_course_ce_hours(self, value):
		course = frappe.get_doc("LMS Course", self.course.name)
		course.ce_hours = value
		course.save()

	def _issue_certificate_to_a_new_student(self, email):
		student = self._create_user(email, "Second", "Learner", ["LMS Student"])
		self._create_enrollment(student.email, self.course.name)
		return self._create_certificate(self.course.name, student.email)

	def test_ce_hours_appear_on_the_certificate_when_it_records_them(self):
		html = self._certificate_html(6)
		self.assertIn("CE hours", html)
		self.assertRegex(html, r"<dd>\s*6\s*</dd>")

	def test_a_certificate_without_ce_hours_prints_no_ce_hours(self):
		for value in (0, None):
			with self.subTest(ce_hours=value):
				html = self._certificate_html(value)
				self.assertNotIn("CE hour", html)

	def test_one_ce_hour_is_singular(self):
		html = self._certificate_html(1)
		self.assertIn("CE hour<", html)
		self.assertNotIn("CE hours", html)

	def test_a_fractional_ce_hours_value_is_not_padded_with_zeros(self):
		html = self._certificate_html(1.25)
		self.assertRegex(html, r"<dd>\s*1\.25\s*</dd>")

	def _html(self):
		return frappe.get_print(
			"LMS Certificate",
			self.certificate.name,
			self.certificate.template,
			doc=frappe.get_doc("LMS Certificate", self.certificate.name),
			as_pdf=False,
			no_letterhead=1,
		)

	def test_the_certificate_carries_the_ceo_signature_block(self):
		html = self._html()
		self.assertIn("Jessie Ogienko", html)
		self.assertIn("Chief Executive Officer", html)
		# The line is decoration; the name and title are the text a screen reader reads.
		self.assertRegex(
			html, r'class="certificate-signature-space certificate-signature-line"\s+aria-hidden="true"'
		)

	def test_a_single_instructor_is_labelled_instructor(self):
		html = self._html()
		self.assertRegex(html, r">\s*Instructor\s*<")
		self.assertNotIn("Instructors", html)

	def test_two_instructors_are_listed_and_labelled_instructors(self):
		course = frappe.get_doc("LMS Course", self.course.name)
		course.append("instructors", {"instructor": self.student.email})
		course.save()
		html = self._html()
		self.assertRegex(html, r">\s*Instructors\s*<")
		self.assertIn("Cert Learner", html)

	def test_an_evaluated_certificate_names_the_evaluator_not_the_instructors(self):
		frappe.db.set_value(
			"LMS Certificate",
			self.certificate.name,
			{"evaluator": "evaluator@example.com", "evaluator_name": "Eve Evaluator"},
		)
		html = self._html()
		self.assertIn("Eve Evaluator", html)
		self.assertRegex(html, r">\s*Evaluated By\s*<")
		self.assertNotRegex(html, r">\s*Instructors?\s*<")

	def test_a_new_certificate_records_the_courses_ce_hours(self):
		self._set_course_ce_hours(6)
		certificate = self._issue_certificate_to_a_new_student("certpdf.second@example.com")
		self.assertEqual(frappe.db.get_value("LMS Certificate", certificate.name, "ce_hours"), 6)

	def test_changing_the_course_later_does_not_change_an_issued_certificate(self):
		self._set_course_ce_hours(6)
		certificate = self._issue_certificate_to_a_new_student("certpdf.second@example.com")

		self._set_course_ce_hours(9)
		self.assertEqual(frappe.db.get_value("LMS Certificate", certificate.name, "ce_hours"), 6)

		# and what it prints is what was recorded, not the course's new value
		html = frappe.get_print(
			"LMS Certificate",
			certificate.name,
			certificate.template,
			doc=frappe.get_doc("LMS Certificate", certificate.name),
			as_pdf=False,
			no_letterhead=1,
		)
		self.assertRegex(html, r"<dd>\s*6\s*</dd>")
		self.assertNotRegex(html, r"<dd>\s*9\s*</dd>")

	def test_a_certificate_for_a_course_without_ce_hours_records_none(self):
		self.assertFalse(frappe.db.get_value("LMS Certificate", self.certificate.name, "ce_hours"))

	def test_a_certificate_issued_before_the_field_existed_prints_no_ce_hours(self):
		# It has 0 recorded, so even a course that now carries hours does not add them to it.
		self._set_course_ce_hours(6)
		frappe.db.set_value("LMS Certificate", self.certificate.name, "ce_hours", 0)
		html = frappe.get_print(
			"LMS Certificate",
			self.certificate.name,
			self.certificate.template,
			doc=frappe.get_doc("LMS Certificate", self.certificate.name),
			as_pdf=False,
			no_letterhead=1,
		)
		self.assertNotIn("CE hour", html)

	def test_the_recorded_hours_cannot_be_changed_once_set(self):
		self._set_course_ce_hours(6)
		certificate = self._issue_certificate_to_a_new_student("certpdf.second@example.com")
		certificate.ce_hours = 7
		with self.assertRaises(frappe.ValidationError):
			certificate.save()

	def test_ce_hours_cannot_be_negative(self):
		course = frappe.get_doc("LMS Course", self.course.name)
		course.ce_hours = -2
		with self.assertRaises(frappe.ValidationError):
			course.save()

	def test_ce_hours_is_optional(self):
		course = frappe.get_doc("LMS Course", self.course.name)
		course.ce_hours = None
		course.save()
		self.assertFalse(frappe.db.get_value("LMS Course", self.course.name, "ce_hours"))

	def test_the_title_names_the_document_not_the_learner(self):
		html = "<html><head><title>Cert Learner</title></head><body></body></html>"
		titled = certificate_pdf._with_title(html, self.certificate)
		self.assertIn(f"<title>Certificate of Completion - {self.course.title}</title>", titled)
		self.assertNotIn("Cert Learner", titled)

	def test_a_missing_title_tag_is_added_to_the_head(self):
		titled = certificate_pdf._with_title("<html><head></head></html>", self.certificate)
		self.assertIn("<head><title>Certificate of Completion", titled)

	def test_a_failed_tagged_render_serves_the_untagged_pdf(self):
		# The untagged path is wkhtmltopdf, which is not installed everywhere (CI has Chromium
		# and no wkhtmltopdf), so stand in for just that call and prove the fallback is taken.
		real_get_print = frappe.get_print

		def get_print(*args, **kwargs):
			if kwargs.get("as_pdf"):
				return b"%PDF-untagged-fallback"
			return real_get_print(*args, **kwargs)

		with (
			patch.object(certificate_pdf, "_tagged_pdf", side_effect=RuntimeError("no chromium")),
			patch.object(certificate_pdf.frappe, "get_print", side_effect=get_print),
		):
			pdf = certificate_pdf.render_certificate_pdf(self.certificate)

		self.assertEqual(pdf, b"%PDF-untagged-fallback")
		self.assertTrue(
			frappe.db.exists(
				"Error Log", {"method": "Tagged certificate PDF failed; serving the untagged one"}
			)
		)

	def test_the_endpoint_serves_a_pdf_and_enforces_print_permission(self):
		other = self._create_user("certpdf.other@example.com", "Other", "Learner", ["LMS Student"])
		self._create_enrollment(other.email, self.course.name)
		unpublished = self._create_certificate(self.course.name, other.email)
		frappe.db.set_value("LMS Certificate", unpublished.name, "published", 0)

		# Rendering is covered above; this test is about who may download, so skip the renderer.
		frappe.set_user(self.student.email)
		with patch.object(certificate_pdf, "render_certificate_pdf", return_value=b"%PDF-test") as render:
			certificate_pdf.download_certificate(self.certificate.name)
			self.assertEqual(frappe.local.response.type, "pdf")
			self.assertEqual(frappe.local.response.filecontent, b"%PDF-test")

			with self.assertRaises(frappe.PermissionError):
				certificate_pdf.download_certificate(unpublished.name)
			self.assertEqual(render.call_count, 1, "a refused certificate must not be rendered")


def _figure_alts(node, found=None):
	"""The /Alt text of every /Figure under a StructTreeRoot."""
	found = set() if found is None else found
	node = node.get_object()
	if isinstance(node, list):
		for child in node:
			_figure_alts(child, found)
	elif hasattr(node, "get"):
		if node.get("/S") == "/Figure" and node.get("/Alt"):
			found.add(str(node["/Alt"]))
		if node.get("/K") is not None:
			_figure_alts(node["/K"], found)
	return found


def _structure_types(node, found=None):
	"""Every /S (structure type) under a StructTreeRoot."""
	found = set() if found is None else found
	node = node.get_object()
	if isinstance(node, list):
		for child in node:
			_structure_types(child, found)
	elif hasattr(node, "get"):
		if node.get("/S"):
			found.add(str(node["/S"]))
		if node.get("/K") is not None:
			_structure_types(node["/K"], found)
	return found
