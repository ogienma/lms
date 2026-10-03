"""Seed a local site with the learner-journey data the accessibility specs walk.

Run: bench --site <site> execute lms.tests.a11y_seed.seed

Idempotent. Creates a throwaway learner, enrols it in the first published
course, adds a text assignment and a certificate, and writes the learner's
generated credentials plus the route map to playwright/.auth/a11y-seed.json
(gitignored) for e2e/a11y/ to read. Local dev sites only.
"""

import json
import os
import secrets

import frappe
from frappe.utils.password import update_password

LEARNER = "a11y.learner@example.test"
ASSIGNMENT_TITLE = "Accessibility walkthrough assignment"
LESSON_TITLE = "Accessibility walkthrough lesson"
OUT = os.environ.get("A11Y_SEED_OUT", "playwright/.auth/a11y-seed.json")


def seed():
	if not frappe.conf.developer_mode:
		frappe.throw("a11y_seed only runs on developer_mode sites")

	course = frappe.db.get_value("LMS Course", {"published": 1}, ["name", "title"], as_dict=True)
	if not course:
		frappe.throw("No published course to seed against")

	if frappe.db.exists("User", LEARNER):
		user = frappe.get_doc("User", LEARNER)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": LEARNER,
				"first_name": "A11y",
				"last_name": "Learner",
				"user_type": "Website User",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	user.add_roles("LMS Student")

	password = secrets.token_urlsafe(18)
	update_password(LEARNER, password)

	if not frappe.db.exists("LMS Enrollment", {"member": LEARNER, "course": course.name}):
		frappe.get_doc({"doctype": "LMS Enrollment", "member": LEARNER, "course": course.name}).insert(
			ignore_permissions=True
		)

	assignment = frappe.db.get_value("LMS Assignment", {"title": ASSIGNMENT_TITLE})
	if not assignment:
		assignment = (
			frappe.get_doc(
				{
					"doctype": "LMS Assignment",
					"title": ASSIGNMENT_TITLE,
					"type": "Text",
					"course": course.name,
					"question": "<p>Describe one thing you learned in this course.</p>",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	# A learner only reaches an assignment through a lesson that embeds it (the
	# assessment access predicates read the lesson's placement rows), so put it in
	# one at the end of the quiz chapter.
	chapter = frappe.get_all(
		"Course Chapter", filters={"course": course.name}, pluck="name", order_by="name"
	)[-1]
	lesson = frappe.db.get_value("Course Lesson", {"title": LESSON_TITLE, "chapter": chapter})
	if not lesson:
		lesson_doc = frappe.get_doc(
			{
				"doctype": "Course Lesson",
				"title": LESSON_TITLE,
				"chapter": chapter,
				"course": course.name,
				"content": json.dumps(
					{
						"blocks": [
							{"id": "a11yasg001", "type": "assignment", "data": {"assignment": assignment}}
						]
					}
				),
			}
		).insert(ignore_permissions=True)
		lesson = lesson_doc.name
		chapter_doc = frappe.get_doc("Course Chapter", chapter)
		chapter_doc.append("lessons", {"lesson": lesson})
		chapter_doc.save(ignore_permissions=True)
	chapter_lessons = frappe.get_all(
		"Lesson Reference", filters={"parent": chapter}, pluck="lesson", order_by="idx"
	)
	assignment_lesson = [chapter, chapter_lessons.index(lesson) + 1]

	certificate = frappe.db.get_value("LMS Certificate", {"member": LEARNER, "course": course.name})
	if not certificate:
		cert = frappe.get_doc(
			{
				"doctype": "LMS Certificate",
				"member": LEARNER,
				"course": course.name,
				"issue_date": frappe.utils.today(),
				"template": "Certificate",
			}
		)
		cert.flags.ignore_validate = True
		certificate = cert.insert(ignore_permissions=True).name

	frappe.db.commit()

	quiz_lesson = frappe.db.get_value(
		"Course Lesson",
		{"course": course.name, "content": ["like", "%quiz%"]},
		["chapter", "name"],
		as_dict=True,
	)
	chapters = frappe.get_all(
		"Course Chapter", filters={"course": course.name}, pluck="name", order_by="name"
	)

	os.makedirs(os.path.dirname(OUT), exist_ok=True)
	with open(OUT, "w") as f:
		json.dump(
			{
				"user": LEARNER,
				"password": password,
				"course": course.name,
				"username": frappe.db.get_value("User", LEARNER, "username"),
				"assignment": assignment,
				"assignmentLesson": assignment_lesson,
				"certificate": certificate,
				"quiz": frappe.db.get_value("LMS Quiz", {}, "name"),
				"chapters": chapters,
				"quizLesson": quiz_lesson,
			},
			f,
			indent=2,
		)
	os.chmod(OUT, 0o600)
	print(f"seeded; wrote {OUT}")
