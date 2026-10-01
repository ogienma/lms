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
| 1 | Certificate (PDF) | untagged PDF, no document language | blocker | LMS print format + wkhtmltopdf | Fix in LMS: needs a tagged-PDF route, or an accessible HTML certificate beside the PDF |
| 2 | Login | `image-alt` | critical | Frappe framework login template | LMS can override the template, or accept |
| 3 | Login | `color-contrast` (labels, "Forgot password?") | serious | Frappe framework login template | Same as 2 |
| 4 | Certificate print view | `color-contrast` ("Instructor" label, `color: gray`) | serious | LMS print format | Fix in LMS |
| 5 | Course detail, lesson | `aria-allowed-attr`, `aria-prohibited-attr` | critical / serious | YouTube embed | Third party, not fixable here; consider a non-iframe fallback |
| 6 | Course list, lesson, quiz, assignment, certificates | `color-contrast` flagged "needs review" (1-6 nodes each) | unknown | LMS / frappe-ui | Axe could not decide, usually text over images or gradients; check by hand |
| 7 | Lesson, certificates | `aria-valid-attr-value` "needs review" | unknown | LMS / frappe-ui | Check by hand |
| 8 | Certificate print view | `bypass` "needs review" | unknown | LMS print format | Trivial for a single-page print view |

Clean on the automated scan: course list, quiz start screen, quiz question view,
assignment lesson, assignment submission.

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
2. Run the NVDA / VoiceOver pass against the same pages and record it next to this file.
3. Turn on `FAIL_ON_VIOLATIONS` in CI once the LMS-owned items are fixed.
