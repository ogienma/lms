import json

from frappe.tests import UnitTestCase

from lms.lms.image_alt_audit import html_images_missing_alt, lesson_images_missing_alt


class TestImageAltAudit(UnitTestCase):
	def test_html_reports_only_images_without_alt(self):
		html = '<img src="a.png"><img src="b.png" alt="A cat"><img src="c.png" alt="">'
		self.assertEqual(html_images_missing_alt(html), ["a.png"])

	def test_html_without_images_is_clean(self):
		self.assertEqual(html_images_missing_alt("<p>text</p>"), [])
		self.assertEqual(html_images_missing_alt(None), [])

	def test_lesson_image_blocks(self):
		blocks = [
			{"type": "image", "data": {"url": "no-alt.png", "caption": "x"}},
			{"type": "image", "data": {"url": "ok.png", "alt": "A dog"}},
			{"type": "image", "data": {"url": "deco.png", "alt": "", "decorative": True}},
			{"type": "image", "data": {"url": "empty.png", "alt": "", "decorative": False}},
			{"type": "image", "data": {"url": "blank.png", "alt": "  "}},
			{"type": "paragraph", "data": {"text": '<img src="inline.png">'}},
		]
		result = lesson_images_missing_alt(json.dumps({"blocks": blocks}))
		self.assertEqual(result, ["no-alt.png", "empty.png", "blank.png", "inline.png"])

	def test_lesson_content_that_is_not_json(self):
		self.assertEqual(lesson_images_missing_alt("not json"), [])
		self.assertEqual(lesson_images_missing_alt(None), [])
