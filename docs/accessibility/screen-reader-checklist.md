# Screen-reader walkthrough checklist (issue #35)

Manual pass over the learner journey with NVDA (Windows) and VoiceOver (macOS and iOS).
Automated axe results are in [README.md](README.md); this covers what axe cannot see:
reading order, announcements, focus, keyboard operation, and whether a task can be
finished by ear.

Record results in a copy of [findings-template.md](findings-template.md), one finding per
problem. The pass is done when every step below is ticked or has a finding.

## 1. Set up

**Test data.** On the local bench, seed a learner and read the generated login:

```bash
bench --site lms.localhost execute lms.tests.a11y_seed.seed
cat playwright/.auth/a11y-seed.json   # user, password, course, assignment, certificate
```

The seed gives you: one published course, a quiz lesson, a lesson with an assignment, and
one issued certificate. It does not submit a quiz or assignment; you will do that in steps 6
and 8.

**Pairings to test** (screen readers behave differently per browser, so name the pair):

| Screen reader | Browser | Required |
|---|---|---|
| NVDA (latest stable) | Firefox | Yes |
| NVDA | Chrome | Yes |
| VoiceOver macOS | Safari | Yes |
| VoiceOver iOS | Safari | Yes: at least login, a lesson and the quiz |
| JAWS | Chrome | No, if available |

Record the exact versions in each finding.

**Speech capture.** Reading back from memory misses things. In NVDA turn on *Tools > Speech
Viewer* and copy the lines into the finding. On macOS use *VoiceOver Utility > Caption
Panel* (or the VO caption panel) for the same.

**Start state.** Fresh browser profile or private window, 100% zoom, no extensions. Close
the browser's own reader mode and any translation bar.

### Keys you will use

| | NVDA (browse mode) | VoiceOver macOS | VoiceOver iOS |
|---|---|---|---|
| Read all | NVDA+Down | VO+A | Two-finger swipe up |
| Next / previous heading | H / Shift+H | VO+Cmd+H | Rotor: Headings, then swipe up/down |
| Landmark list or jump | D / Shift+D | VO+U, then Landmarks | Rotor: Landmarks |
| Links, buttons, form fields | K, B, F | VO+U | Rotor |
| Element list | NVDA+F7 | VO+U | Rotor |
| Toggle browse / focus mode | NVDA+Space | n/a | n/a |
| Activate | Enter or Space | VO+Space | Double-tap |
| Stop speech | Ctrl | Ctrl | Two-finger tap |

`NVDA` is Insert or Caps Lock, whichever you configured. `VO` is Ctrl+Option.

**Rules of thumb for this pass:**
- First go through each page *by ear only*, screen off or eyes away, if you can. If a step
  cannot be done without looking, that is a finding.
- Then repeat the same step keyboard-only without the screen reader. Tab order and focus
  visibility are failures in their own right.
- Note what is announced, not what you expect. Quote the speech, not your summary.

## 2. Checks that apply to every page

Run these once per page in the journey; do not repeat them in the step lists below unless
something is page-specific.

- [ ] **Page title** is announced on load and says where you are (not just "Frappe").
- [ ] **Skip link.** First Tab stop is "Skip to main content", and it moves focus past the
      sidebar to the main content.
- [ ] **Landmarks** exist: banner, navigation, main. There is exactly one main.
- [ ] **Headings** form an outline: one h1, no skipped levels, and the h1 names the page.
- [ ] **Route change.** After a link navigates within the app (no full reload), the screen
      reader announces the new page or focus lands somewhere sensible. Silence after
      activating a link is a finding.
- [ ] **Focus order** follows reading order; **focus is always visible**.
- [ ] **No keyboard trap.** You can leave every widget with Tab, Shift+Tab or Esc.
- [ ] **Controls have names and roles.** Icon-only buttons say what they do. Nothing is
      announced as just "button", "link" or "clickable" with no name.
- [ ] **Images and icons.** Informative images have text; decorative ones are silent.
- [ ] **Language.** Speech uses the right voice (the page language is `en`).

## 3. Walkthrough

Use `<course>` for the `course` value in the seed file. Base URL `http://lms.localhost:8000`.

### 3.1 Login: `/login`

(This is Frappe's login template, not LMS code. Report it anyway; the owner column in the
findings decides who fixes it.)

- [ ] Logo: announced as an image with a name, or skipped. Axe flagged it for no alt text.
- [ ] Email and Password fields: each announces its label. "Forgot password?" is a link.
- [ ] Submit the form empty. Is the error announced, and does focus go to it or the first
      bad field?
- [ ] Submit a wrong password. Same questions.
- [ ] Log in with the seeded learner. Where does focus land, and is the destination announced?

### 3.2 Course list: `/lms/courses`

- [ ] Course cards: each is one clear stop (title, then details), not a pile of unlabelled
      links. Navigate by link (K) and by heading (H) and compare.
- [ ] Search and filters: label, role, and whether results updating is announced.
- [ ] The onboarding / "Complete your profile" prompt, if shown: is it a dialog? Does
      focus move into it, stay trapped, return on close, and does Esc close it?
- [ ] Open the command palette (Ctrl+K), notifications and the user menu: each opens, is
      operable by keyboard, and closes with Esc returning focus to its trigger.

### 3.3 Course page: `/lms/courses/<course>`

- [ ] Title, instructor, rating, enrolment state read in a sensible order.
- [ ] The course outline (chapters and lessons): is it a list or tree with a name for each
      item? Can you tell which lesson is complete and which is current?
- [ ] The preview video (YouTube embed): can you find it, pause it and reach the controls?
      The ARIA errors inside it are the embed's, but check the user can still get past it.
- [ ] Breadcrumbs: the "..." overflow button, if present, has a name (frappe-ui#1205).
- [ ] The enrol / continue button: name and result of activating it are clear.

### 3.4 Lesson: `/lms/courses/<course>/learn/1-1`

- [ ] Lesson title is the h1; the body uses real headings and lists.
- [ ] Previous / Next / Back to Course buttons are named and in a logical order.
- [ ] Embedded video: reachable, controls named, captions available or an alternative given.
- [ ] Marking a lesson complete or moving on: is progress change announced?
- [ ] Sidebar outline: you can jump to another lesson by keyboard and know where you are.
- [ ] The sidebar collapse control states whether it is expanded.

### 3.5 Quiz start: `/lms/courses/<course>/learn/3-1`

- [ ] The quiz summary (questions, time limit, pass mark, attempts) reads as a list or
      table with labels, not loose numbers.
- [ ] "Start Quiz" is a button with a clear name.
- [ ] After pressing it, the screen reader announces the first question, or focus moves to it.

### 3.6 Quiz questions: `/lms/quiz/<quiz>`

This is the highest-risk page. Take your time.

- [ ] Each question reads: number, marks, "Choose one answer" (or "Choose all that apply"),
      then the question text, then the options.
- [ ] **Options are a group.** Single-answer options announce as radio buttons in a group
      with the question as the group name ("1 of 4", selected/not selected). Multiple-answer
      options announce as checkboxes. If options are announced as plain text or buttons
      with no state, that is blocking.
- [ ] Choosing an option announces the new state.
- [ ] "Mark for Review" is a toggle that announces on/off.
- [ ] Next, Previous and the question navigator: named, operable, and the current question
      is announced when it changes.
- [ ] Question counter ("Question 1 of 8") is announced on change (live region), or focus
      moves to the new question.
- [ ] Timer, if the quiz has a time limit: it can be read on demand, and low time is
      announced without stealing focus.
- [ ] **Submit.** Confirm-dialog (if any): focus moves in, is trapped, returns on cancel.
- [ ] **Result screen.** Pass or fail, score, and per-question correctness are announced in
      words and not only by colour or an icon. Axe did not scan this page: check it by hand
      and run axe on it too.
- [ ] Retry attempt: the flow can be repeated.

### 3.7 Assignment in a lesson: `/lms/courses/<course>/learn/3-2`

- [ ] The assignment block is announced as an assignment with its title, and its question
      text is in the reading order.
- [ ] The link or button to submit is named, and says what it opens.

### 3.8 Assignment submission: `/lms/assignment-submission/<assignment>/new`

- [ ] Breadcrumb and title are read; the question text is read before the answer field.
- [ ] The answer field (a rich-text editor for the Text type): announced with a name and
      role, and you can type, format and leave it by keyboard. Does the editor trap Tab?
- [ ] For other assignment types (PDF, URL, Image, Document): file or URL input has a label.
- [ ] Submit with an empty answer. Is the validation message announced and linked to the field?
- [ ] Submit a real answer. Is success announced (toast or page change)? A silent success
      is a finding (frappe-ui#642).
- [ ] After submission, the submitted state and any grade or feedback are readable.

### 3.9 Certificates list: `/lms/user/<username>/certificates`

- [ ] The learner's certificates read as a list; each item names the course and the date.
- [ ] The download / view link is named for the certificate it opens ("Download certificate
      for <course>"), not an anonymous "Download" repeated.
- [ ] Activating it: you are told a PDF is opening, and focus is not lost in a blank tab.

### 3.10 Certificate PDF

Open the PDF from the link in 3.9. Test in at least: Chrome or Edge's built-in viewer with
NVDA, and Preview or Safari with VoiceOver. Adobe Reader with NVDA if you have it.

- [ ] The **document title** is announced: "Certificate of Completion - <course>", not the
      learner's name.
- [ ] **Language** is correct (`en`): the voice is right.
- [ ] **Headings:** H jumps to "Certificate of Completion".
- [ ] **Reading order** is: organisation, heading, "This is to certify that", learner name,
      "has successfully completed the <course> course including all required assessments on
      <date>", the Instructor label, then the instructor name.
- [ ] Nothing is read twice or as "blank", and the decorative logo is silent.
- [ ] Repeat for a certificate issued **by an evaluator**, which shows "Evaluated By"
      instead of "Instructor" (seed does not create one).
- [ ] If Chromium is unavailable the endpoint serves the older untagged PDF. If you can
      stop it (rename `chromium_path`), confirm the fallback still downloads, and note that
      it will fail these checks.

## 4. Axe "needs review" items

Axe could not decide these. They were checked by script rather than by ear, so there is
nothing to do here unless a page changes:

- **Contrast (15 nodes):** `node e2e/a11y/contrast_review.mjs` samples the real pixels behind
  each node's text and computes the contrast against the worst one. All pass; the lowest is
  5.5:1. `node e2e/a11y/contrast_review.mjs --control` first proves the measuring code fails
  known-bad text, including on gradients, and passes known-good text. Re-run both after any
  colour or layout change. Results: `contrast-review.json`.
- **`aria-valid-attr-value` (2 nodes):** one false alarm (Plyr), one empty `aria-controls` on
  a closed Reka UI popover trigger. See README findings 6 and 7.

**Still by hand:** the video controls over a bright video frame. The script measures the
unloaded player, which is black. Play a video with a bright frame, pause it, and check the
time and button labels in the control bar against the 4.5:1 line with a contrast picker.
Anything below 4.5:1 for body text (3:1 for large text and UI components) is a finding.

## 5. Beyond the happy path

Quick checks, once each, not per page:

- [ ] **200% zoom and 320px width.** Content reflows with no horizontal scroll and nothing
      is cut off (WCAG 1.4.10).
- [ ] **Dark theme.** Switch theme if offered and spot-check contrast on the course list,
      quiz and lesson.
- [ ] **Reduced motion.** With the OS setting on, no essential animation remains.
- [ ] **Browser reader mode.** In Firefox Reader View or Safari Reader, a lesson reads
      cleanly (the issue's "native browser readers are enough" assumption). Note what is
      lost: embedded quizzes, code blocks, images.
- [ ] **Zoomed text only** (browser text size 200%, page zoom off).

## 6. Wrap-up

- [ ] Every finding is in the findings file with severity, owner and a decision.
- [ ] Re-run the axe scan after any fix and attach the new `axe-summary.md`.
- [ ] Update the findings table in README.md and the status in issue #35.
- [ ] Decide, and record, whether the "done when" is met: no blocking findings on the
      learner journey, or a tracked list of the remaining ones with owners.
