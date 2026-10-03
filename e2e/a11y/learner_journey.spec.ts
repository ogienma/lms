import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { baseURL } from "../config";

// Axe baseline for the learner journey in issue #35: login -> course list ->
// lesson -> quiz -> assignment -> certificate. Report-only for now: it records
// every violation to docs/accessibility/ and fails only if a page can't be
// scanned. Flip FAIL_ON_VIOLATIONS=1 once the baseline is triaged.
//
// Needs the seed from lms/tests/a11y_seed.py (a throwaway learner plus an
// assignment and certificate); its output holds generated credentials, so it
// lives under the gitignored playwright/.auth/.

const seedFile = process.env.A11Y_SEED || "playwright/.auth/a11y-seed.json";
const seed = JSON.parse(readFileSync(seedFile, "utf8"));
const OUT_DIR = process.env.A11Y_OUT || "docs/accessibility";
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

type Page = {
	id: string;
	path: string;
	// Text that proves the page this step is about, not its shell or a 404.
	ready: string | RegExp;
	guest?: boolean;
	// Extra interaction before the scan, for states a plain load never shows.
	before?: (page: import("@playwright/test").Page) => Promise<void>;
};

const chapterNo = (name: string) => parseInt(name.split(" ")[0], 10);
const [qChapter] = [seed.quizLesson.chapter as string];
const [aChapter, aIndex] = seed.assignmentLesson as [string, number];
const learn = (chapter: string, lesson: number) =>
	`/lms/courses/${seed.course}/learn/${chapterNo(chapter)}-${lesson}`;

const PAGES: Page[] = [
	{ id: "login", path: "/login", ready: /log in|login/i, guest: true },
	{ id: "course-list", path: "/lms/courses", ready: "Courses" },
	{ id: "course-detail", path: `/lms/courses/${seed.course}`, ready: /A guide to Frappe Learning/ },
	{ id: "lesson", path: learn(seed.chapters[0], 1), ready: /Introduction/ },
	{ id: "quiz-lesson", path: learn(qChapter, 1), ready: "Start Quiz" },
	{
		id: "quiz-question",
		path: `/lms/quiz/${seed.quiz}`,
		ready: "Question 1 of",
		before: async (page) => {
			await page.getByRole("button", { name: /start quiz/i }).click();
		},
	},
	{ id: "assignment-lesson", path: learn(aChapter, aIndex), ready: "Accessibility walkthrough" },
	{
		id: "assignment-submission",
		path: `/lms/assignment-submission/${seed.assignment}/new`,
		ready: /Describe one thing you learned/,
	},
	{ id: "certificates", path: `/lms/user/${seed.username}/certificates`, ready: /certificate/i },
	{
		id: "certificate-print-view",
		path: `/printview?doctype=LMS%20Certificate&name=${seed.certificate}&format=Certificate&no_letterhead=1`,
		ready: /./,
	},
];

const results: Record<string, unknown>[] = [];

test.describe.configure({ mode: "serial" });

test.use({ baseURL });

test.beforeAll(() => mkdirSync(OUT_DIR, { recursive: true }));

test.afterAll(() => {
	writeFileSync(
		`${OUT_DIR}/axe-results.json`,
		JSON.stringify({ scannedAt: new Date().toISOString(), tags: TAGS, results }, null, 2)
	);
	const rows = results
		.map((r: any) => {
			const v = r.violations as any[];
			const by = (i: string) => v.filter((x) => x.impact === i).length;
			return `| ${r.id} | ${r.url} | ${by("critical")} | ${by("serious")} | ${by("moderate")} | ${by("minor")} | ${(r.incomplete as any[]).length} |`;
		})
		.join("\n");
	writeFileSync(
		`${OUT_DIR}/axe-summary.md`,
		`# Axe baseline (${new Date().toISOString().slice(0, 10)})\n\nTags: ${TAGS.join(", ")}\n\n| Page | URL | Critical | Serious | Moderate | Minor | Needs review |\n|---|---|---|---|---|---|---|\n${rows}\n`
	);
});

for (const p of PAGES) {
	test(`axe: ${p.id}`, async ({ browser }) => {
		const context = await browser.newContext({ baseURL });
		const page = await context.newPage();
		try {
			if (!p.guest) {
				const res = await context.request.post("/api/method/login", {
					form: { usr: seed.user, pwd: seed.password },
				});
				expect(res.ok(), "learner login").toBeTruthy();
			}
			await page.goto(p.path, { waitUntil: "networkidle" });
			await p.before?.(page);
			await expect(page.locator("body")).toContainText(p.ready, { timeout: 20000 });
			await expect(page.locator("body")).not.toContainText(/page not found/i);
			// Let the SPA settle (lazy route chunks, skeletons) before scanning.
			await page.waitForTimeout(1500);

			const scan = await new AxeBuilder({ page }).withTags(TAGS).analyze();
			results.push({
				id: p.id,
				url: page.url().replace(baseURL, ""),
				violations: scan.violations.map((v) => ({
					id: v.id,
					impact: v.impact,
					help: v.help,
					helpUrl: v.helpUrl,
					nodes: v.nodes.map((n) => ({ target: n.target, html: n.html.slice(0, 200) })),
				})),
				incomplete: scan.incomplete.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length })),
			});
			if (process.env.FAIL_ON_VIOLATIONS) expect(scan.violations).toEqual([]);
		} finally {
			await context.close();
		}
	});
}

// The certificate itself is a PDF (www/certificate.py redirects to
// lms.lms.certificate_pdf), which axe cannot read. A tagged PDF carries a structure tree
// and a document language; wkhtmltopdf output carries neither, so a screen
// reader gets nothing to navigate. Recorded alongside the axe results.
test("pdf: certificate tagging", async ({ browser }) => {
	const context = await browser.newContext({ baseURL });
	try {
		await context.request.post("/api/method/login", { form: { usr: seed.user, pwd: seed.password } });
		const res = await context.request.get(
			`/api/method/lms.lms.certificate_pdf.download_certificate?name=${seed.certificate}`
		);
		expect(res.ok()).toBeTruthy();
		const raw = (await res.body()).toString("latin1");
		const pdf = {
			bytes: raw.length,
			tagged: raw.includes("/StructTreeRoot"),
			markedContent: raw.includes("/MarkInfo"),
			language: /\/Lang\s*[(<]/.test(raw),
		};
		writeFileSync(`${OUT_DIR}/certificate-pdf.json`, JSON.stringify(pdf, null, 2));
		if (process.env.FAIL_ON_VIOLATIONS) expect(pdf.tagged && pdf.language).toBeTruthy();
	} finally {
		await context.close();
	}
});
