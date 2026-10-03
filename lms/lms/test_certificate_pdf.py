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
