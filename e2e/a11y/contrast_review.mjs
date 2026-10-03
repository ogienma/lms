// Measures the real contrast of every node axe reports as "needs review" for
// color-contrast. Axe gives up when text sits on an image, gradient or
// translucent layer; this does not, it samples the pixels.
//
// For each such node: read the text colour, hide the text, screenshot the node's
// box, and take the lightest and darkest background pixels. Contrast is then
// computed against the worst of the two, so a pass means every pixel behind the
// text passes. Run after seeding:
//   PLAYWRIGHT_BASE_URL=http://lms.localhost:8000 node e2e/a11y/contrast_review.mjs
//
// Usage: node e2e/a11y/contrast_review.mjs [pageId ...]   (default: all)

import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

const base = process.env.PLAYWRIGHT_BASE_URL || "http://lms.localhost:8000";
const seed = JSON.parse(
	readFileSync(
		process.env.A11Y_SEED || "playwright/.auth/a11y-seed.json",
		"utf8"
	)
);
const OUT = process.env.A11Y_OUT || "docs/accessibility";

const chapterNo = (n) => parseInt(n.split(" ")[0], 10);
const learn = (c, l) =>
	`/lms/courses/${seed.course}/learn/${chapterNo(c)}-${l}`;
const PAGES = [
	{ id: "course-list", path: "/lms/courses" },
	{ id: "course-detail", path: `/lms/courses/${seed.course}` },
	{ id: "lesson", path: learn(seed.chapters[0], 1) },
	{
		id: "quiz-question",
		path: `/lms/quiz/${seed.quiz}`,
		before: (p) => p.getByRole("button", { name: /start quiz/i }).click(),
	},
	{
		id: "assignment-lesson",
		path: learn(seed.assignmentLesson[0], seed.assignmentLesson[1]),
	},
	{ id: "certificates", path: `/lms/user/${seed.username}/certificates` },
];
const only = process.argv.slice(2);

const lin = (c) => {
	const s = c / 255;
	return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
};
const lum = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
const ratio = (a, b) => {
	const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
	return (hi + 0.05) / (lo + 0.05);
};
// rgba -> rgb over a backdrop
const over = ([r, g, b, a], [br, bg, bb]) => [
	r * a + br * (1 - a),
	g * a + bg * (1 - a),
	b * a + bb * (1 - a),
];

async function pngPixels(page, buffer) {
	// Decode in the page: canvas getImageData on a data URL of the screenshot.
	return page.evaluate(async (b64) => {
		const img = new Image();
		img.src = "data:image/png;base64," + b64;
		await img.decode();
		const c = document.createElement("canvas");
		c.width = img.width;
		c.height = img.height;
		const ctx = c.getContext("2d");
		ctx.drawImage(img, 0, 0);
		return Array.from(ctx.getImageData(0, 0, c.width, c.height).data);
	}, buffer.toString("base64"));
}

// Reads the text colour of `loc`, samples what is behind it, and fills `row` with the verdict.
async function measure(page, loc, row) {
	await loc.scrollIntoViewIfNeeded({ timeout: 3000 });
	const info = await loc.evaluate((el) => {
		const cs = getComputedStyle(el);
		// getComputedStyle may answer in color(srgb ...) or oklch(...); a 1px canvas
		// converts whatever it is to sRGB 0-255.
		const c = document.createElement("canvas");
		c.width = c.height = 1;
		const x = c.getContext("2d", { willReadFrequently: true });
		x.fillStyle = cs.color;
		x.fillRect(0, 0, 1, 1);
		const d = x.getImageData(0, 0, 1, 1).data;
		return {
			text: (el.innerText || "").trim().slice(0, 60),
			color: cs.color,
			rgba: [d[0], d[1], d[2], d[3] / 255],
			size: parseFloat(cs.fontSize),
			weight: parseInt(cs.fontWeight, 10) || 400,
			opacity: (() => {
				let o = 1;
				for (let e = el; e; e = e.parentElement)
					o *= parseFloat(getComputedStyle(e).opacity);
				return o;
			})(),
		};
	});
	Object.assign(row, info);
	// Hide the text, then look at what is behind it.
	await loc.evaluate((el) => {
		el.__prev = el.style.cssText;
		el.style.setProperty("color", "transparent", "important");
		el.style.setProperty("text-shadow", "none", "important");
		el.querySelectorAll("*").forEach((c) =>
			c.style.setProperty("color", "transparent", "important")
		);
	});
	const shot = await loc.screenshot({ type: "png" });
	await loc.evaluate((el) => (el.style.cssText = el.__prev));
	const px = await pngPixels(page, shot);
	let min = [255, 255, 255],
		max = [0, 0, 0];
	for (let i = 0; i < px.length; i += 4) {
		const c = [px[i], px[i + 1], px[i + 2]];
		if (lum(c) < lum(min)) min = c;
		if (lum(c) > lum(max)) max = c;
	}
	const fg = row.rgba;
	const eff = (bg) => over([fg[0], fg[1], fg[2], fg[3] * row.opacity], bg);
	const worst = Math.min(ratio(eff(min), min), ratio(eff(max), max));
	const large = row.size >= 24 || (row.size >= 18.66 && row.weight >= 700);
	Object.assign(row, {
		bgDarkest: min.map(Math.round).join(","),
		bgLightest: max.map(Math.round).join(","),
		worstRatio: Math.round(worst * 100) / 100,
		need: large ? 3 : 4.5,
		verdict: worst >= (large ? 3 : 4.5) ? "pass" : "FAIL",
	});
}

// Self-test: the same measuring code must fail text that is known to be bad and pass text
// that is known to be fine, on a gradient (the case axe gives up on).
//   node e2e/a11y/contrast_review.mjs --control
if (process.argv.includes("--control")) {
	const cases = [
		{
			name: "#808080 on white (3.95:1)",
			html: '<p style="color:#808080;background:#fff">Sample text</p>',
			expect: "FAIL",
		},
		{
			name: "#595959 on white (7:1)",
			html: '<p style="color:#595959;background:#fff">Sample text</p>',
			expect: "pass",
		},
		{
			name: "#808080 on white-to-grey gradient",
			html: '<p style="color:#808080;background:linear-gradient(90deg,#fff,#bbb)">Sample text, long enough to span the gradient</p>',
			expect: "FAIL",
		},
		{
			name: "white on dark gradient",
			html: '<p style="color:#fff;background:linear-gradient(90deg,#000,#444)">Sample text, long enough to span the gradient</p>',
			expect: "pass",
		},
		{
			name: "#767676 on white (4.54:1, just passes)",
			html: '<p style="color:#767676;background:#fff">Sample text</p>',
			expect: "pass",
		},
		{
			name: "#777777 on white (4.48:1, just fails)",
			html: '<p style="color:#777;background:#fff">Sample text</p>',
			expect: "FAIL",
		},
		{
			name: "oklch grey on white",
			html: '<p style="color:oklch(0.55 0 0);background:#fff">Sample text</p>',
			expect: "pass",
		},
	];
	const b = await chromium.launch();
	const pg = await b.newPage();
	let bad = 0;
	for (const c of cases) {
		await pg.setContent(
			'<body style="margin:0;font:16px sans-serif">' + c.html + "</body>"
		);
		const row = {};
		await measure(pg, pg.locator("p"), row);
		const ok = row.verdict === c.expect;
		if (!ok) bad++;
		console.log(
			(ok ? "ok  " : "BAD ") +
				c.name +
				": got " +
				row.verdict +
				" (" +
				row.worstRatio +
				"), expected " +
				c.expect
		);
	}
	await b.close();
	console.log(bad ? bad + " control(s) wrong" : "all controls right");
	process.exit(bad ? 1 : 0);
}

const browser = await chromium.launch();
const out = [];
for (const p of PAGES) {
	if (only.length && !only.includes(p.id)) continue;
	const ctx = await browser.newContext({
		baseURL: base,
		viewport: { width: 1280, height: 900 },
	});
	await ctx.request.post("/api/method/login", {
		form: { usr: seed.user, pwd: seed.password },
	});
	const page = await ctx.newPage();
	await page.goto(p.path, { waitUntil: "networkidle" });
	await p.before?.(page);
	await page.waitForTimeout(2000);

	const scan = await new AxeBuilder({ page })
		.withRules(["color-contrast"])
		.analyze();
	const nodes = scan.incomplete.flatMap((v) => v.nodes);
	for (const n of nodes) {
		const sel = n.target[n.target.length - 1];
		const loc = page.locator(sel).first();
		const row = {
			page: p.id,
			selector: n.target.join(" >> "),
			reason: n.any?.[0]?.data?.messageKey ?? n.any?.[0]?.message ?? "",
		};
		try {
			await measure(page, loc, row);
		} catch (e) {
			row.verdict = "unmeasured";
			row.error = String(e.message).split("\n")[0];
		}
		out.push(row);
	}
	await ctx.close();
}
await browser.close();

mkdirSync(OUT, { recursive: true });
writeFileSync(`${OUT}/contrast-review.json`, JSON.stringify(out, null, 2));
for (const r of out)
	console.log(
		[
			r.page,
			r.verdict,
			r.worstRatio ?? "-",
			`need ${r.need ?? "-"}`,
			JSON.stringify(r.text ?? ""),
			r.color ?? "",
			r.reason,
			r.selector.slice(-70),
		].join(" | ")
	);
console.log(
	`\n${out.length} nodes: ${
		out.filter((r) => r.verdict === "pass").length
	} pass, ${out.filter((r) => r.verdict === "FAIL").length} fail, ${
		out.filter((r) => r.verdict === "unmeasured").length
	} unmeasured`
);
