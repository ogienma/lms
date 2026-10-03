# Screen-reader findings (issue #35)

Copy this file to `findings-YYYY-MM-DD.md` for a pass and fill it in. Walkthrough steps are
in [screen-reader-checklist.md](screen-reader-checklist.md).

## Session

| | |
|---|---|
| Date | |
| Tester | |
| Instance and commit | e.g. `lms.localhost`, `a11y-certificate-pdf@4ec3dee0` |
| Seed data | `lms.tests.a11y_seed` run? Y / N |
| Pairings tested | e.g. NVDA 2026.x + Firefox NN, VoiceOver macOS NN + Safari NN, VoiceOver iOS NN + Safari |
| Anything not tested, and why | |

## Step results

One row per checklist step. Result: **Pass**, **Fail** (add a finding), **N/A** (say why),
or **Not run**.

| Step | NVDA + Firefox | NVDA + Chrome | VO macOS + Safari | VO iOS + Safari | Finding |
|---|---|---|---|---|---|
| 2 Every page | | | | | |
| 3.1 Login | | | | | |
| 3.2 Course list | | | | | |
| 3.3 Course page | | | | | |
| 3.4 Lesson | | | | | |
| 3.5 Quiz start | | | | | |
| 3.6 Quiz questions and result | | | | | |
| 3.7 Assignment in lesson | | | | | |
| 3.8 Assignment submission | | | | | |
| 3.9 Certificates list | | | | | |
| 3.10 Certificate PDF | | | | | |
| 4 Axe needs-review items | | | | | |
| 5 Zoom, theme, reader mode | | | | | |

## Severity

| Level | Meaning | Blocks "done"? |
|---|---|---|
| **Blocking** | A learner using this screen reader cannot complete the step, or completes it wrongly without knowing (for example an unlabelled answer, a silent failed submit) | Yes |
| **Serious** | The step can be completed, but only with workarounds, guessing or sighted help | Yes, unless a fix is scheduled with an owner |
| **Moderate** | Slower or confusing, but understandable | No |
| **Minor** | Polish: wording, redundancy, order of secondary items | No |

## Owner

Use one value, because it decides who acts:

- **LMS**: our code (`lms/`, `frontend/src/`, the certificate print format). We fix it.
- **frappe-ui**: the component library. We do not patch it; link the upstream issue and
  work around it in an LMS wrapper if it blocks a step.
- **Frappe**: the framework (login page, print views, desk).
- **Third party**: YouTube embed, browser or screen-reader bug.

## Findings

Copy the block below for each finding. IDs run `A11Y-001`, `A11Y-002`, ...

### A11Y-000: short title of the problem

| | |
|---|---|
| **Page and step** | e.g. 3.6 Quiz questions, `/lms/quiz/<quiz>` |
| **Screen reader and browser** | e.g. NVDA 2026.x + Firefox NN. Say if it reproduces elsewhere |
| **Severity** | Blocking / Serious / Moderate / Minor |
| **Owner** | LMS / frappe-ui / Frappe / Third party |
| **WCAG criterion** | e.g. 4.1.2 Name, Role, Value |
| **Axe also flagged it?** | Y (rule id) / N |
| **Upstream issue** | link, if any (for example frappe-ui#642) |

**What I did.** Keys pressed or controls used, in order.

**What was announced.** Quote the speech output (from the Speech Viewer or caption panel),
not a summary:

> ...

**What should have been announced.**

> ...

**Notes.** Screenshot, recording, DOM snippet or selector. If the same problem appears on
other pages, list them here instead of filing it again.

**Decision.** Fix in LMS / Work around in an LMS wrapper / Wait for upstream / Won't fix.
Give the reason. For a fix: branch or PR, and who owns it.

**Status.** Open / In progress / Fixed in `<commit>` and re-tested on `<date>` / Won't fix.

---

## Summary

Fill this in last.

| Severity | LMS | frappe-ui | Frappe | Third party |
|---|---|---|---|---|
| Blocking | | | | |
| Serious | | | | |
| Moderate | | | | |
| Minor | | | | |

**Does the learner journey meet the issue's "done when"?** Yes / No: no blocking findings,
or a tracked list of the remaining ones with owners.

**Open items with owners**

| ID | Title | Severity | Owner | Next step | Due |
|---|---|---|---|---|---|
| | | | | | |
