# Accessibility baseline (issue #35)

Automated axe scan of the learner journey, plus a check of the certificate PDF.
This is the first of the four to-dos in the issue; it does not replace the NVDA /
VoiceOver walkthrough, since axe finds only a minority of real screen-reader
problems.

## Reproduce

```bash
# 1. Seed a throwaway learner, an assignment (placed in a lesson) and a certificate
bench --site lms.localhost execute lms.tests.a11y_seed.seed

# 2. Scan (needs the bench running; Chromium via `npx playwright install chromium`)
PLAYWRIGHT_BASE_URL=http://lms.localhost:8000 npx playwright test --project=a11y
```

Results land in this folder: `axe-summary.md`, `axe-results.json` (every node) and
`certificate-pdf.json`. The seed writes the learner's generated password to
`playwright/.auth/a11y-seed.json` (gitignored). The scan is report-only; set
`FAIL_ON_VIOLATIONS=1` to make it fail on any violation once the baseline is triaged.

## Findings (2026-10-01, local dev site, WCAG 2.0/2.1/2.2 A and AA)

| # | Page | Rule | Impact | Whose code | Verdict |
|---|---|---|---|---|---|
| 1 | Certificate (PDF) | untagged PDF, no document language or title | blocker | LMS print format + wkhtmltopdf | **Fixed.** `lms.lms.certificate_pdf.download_certificate` renders with Chromium and tags the PDF; the print format now uses a real heading and paragraphs. Falls back to the old untagged PDF if Chromium fails |
| 2 | Login | `image-alt` | critical | Frappe framework login template | **Fixed** by `lms/www/login.html`: the logo's alt is the app name |
| 3 | Login | `color-contrast` (labels, "Forgot password?") | serious | Frappe framework login template | **Fixed** (`text-ink-gray-7`, about 11.6:1 on white). `lms/www/login.html` is a copy of Frappe's with only these two edits; `lms/tests/test_login_template.py` fails if Frappe's file changes, so re-sync it on a Frappe upgrade |
| 4 | Certificate print view | `color-contrast` ("Instructor" label, `color: gray`) | serious | LMS print format | **Fixed** (`#595959`, 7:1) |
| 5 | Course detail, lesson | `aria-allowed-attr`, `aria-prohibited-attr` | critical / serious | YouTube embed | Third party, not fixable here; consider a non-iframe fallback |
| 6 | Course list, lesson, quiz, assignment, certificates | `color-contrast` flagged "needs review" (1-6 nodes each) | unknown | LMS / frappe-ui | Axe could not decide, usually text over images or gradients; check by hand |
| 7 | Lesson, certificates | `aria-valid-attr-value` "needs review" | unknown | LMS / frappe-ui | Check by hand |
| 8 | Certificate print view | `bypass` "needs review" | unknown | LMS print format | Cleared by the new heading |

Clean on the automated scan: course list, quiz start screen, quiz question view,
assignment lesson, assignment submission.

## Upstream audit (frappe-ui, searched 2026-10-02)

The "community audit" is five issues filed on 8 May 2026 by two outside contributors,
plus two later ones. All are open and none has a linked fix PR. We pin
`frappe-ui 1.0.0-rc.1`; whether a later release fixes any of them is unchecked.

| Issue | Covers | Learner-facing here? |
|---|---|---|
| [frappe-ui#639](https://github.com/frappe/frappe-ui/issues/639) | Form controls: label/ID association, `aria-invalid` / error linkage, `Switch` semantics, required asterisk read aloud | Yes: assignment and quiz-adjacent forms, login-adjacent flows, profile |
| [frappe-ui#640](https://github.com/frappe/frappe-ui/issues/640) | Dialog / Popover / Tooltip: focus trap and restore, `role="dialog"`, Escape, hoverable tooltips | Yes: any modal a learner opens (the lesson and quiz flows use dialogs) |
| [frappe-ui#641](https://github.com/frappe/frappe-ui/issues/641) | Select / combobox / navigation patterns (4.1.2, 2.1.1) | Likely: course filters, search; not yet read |
| [frappe-ui#642](https://github.com/frappe/frappe-ui/issues/642) | Toast / Alert / Progress: no live regions, no `progressbar` role | Yes: quiz and assignment feedback toasts, course progress bars |
| [frappe-ui#643](https://github.com/frappe/frappe-ui/issues/643) | Global focus ring, contrast, icons | Yes, and overlaps the `color-contrast` "needs review" items above; not yet read |
| [frappe-ui#1205](https://github.com/frappe/frappe-ui/issues/1205) | Dropdown switch items, ContextMenu keyboard, Password toggle is a `<span>`, Breadcrumbs "…" unnamed | Partly: Password (login/profile), Breadcrumbs (shown on every page we scanned) |
| [frappe-ui#1036](https://github.com/frappe/frappe-ui/issues/1036) | Charts: confirm `role="img"` plots work in NVDA and JAWS | Statistics page only, not learner journey |

These are reported by outsiders and not verified by us. The axe scan did not flag
any of them, which is expected: they are keyboard, focus and announcement problems
that axe cannot see. They are the main reason the manual NVDA / VoiceOver pass matters.
No issue exists in `frappe/lms` for this (only #730, closed, from 2024).

Because we only fix `lms` code, the frappe-ui items stay upstream. Where one blocks a
learner step in the walkthrough, work around it in an LMS wrapper rather than patching
frappe-ui.

## Not covered yet

- Quiz result / review screen and a submitted assignment (the scan does not submit).
- Keyboard-only flow, focus order and focus after route changes. Axe cannot see these.
- Live regions: whether quiz feedback and SPA navigation are announced.
- Lesson media: captions on uploaded video, the editor's rendered blocks.
- One course, one learner. Pages with a different shape (SCORM chapters, batches,
  programs, programming exercises) are not scanned.
- Mobile layout and 200% zoom / reflow.
- Dark theme contrast.

## Next

1. Triage 6 and 7 by hand, then 2-4 and 1 into fix / won't-fix.
2. Run the NVDA / VoiceOver pass against the same pages: follow
   [screen-reader-checklist.md](screen-reader-checklist.md) and record results in a copy of
   [findings-template.md](findings-template.md) next to this file.
3. Turn on `FAIL_ON_VIOLATIONS` in CI once the LMS-owned items are fixed.
