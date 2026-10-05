# Course creator checklist: accessibility and EMDRIA

Use this before you publish a course, and again for the review. It covers what the
platform cannot check for you. Anything not ticked means the course is not ready.

Why these rules exist: EMDRIA requires that video has closed captions and that every
image has alternative text. The platform does not enforce either one, so this checklist
is the safeguard. (Tracked in issues #37 and #34.)

## 1. Video: captions are required

**The rule:** all lesson video is hosted on **YouTube, set to Unlisted**, and has
**accurate captions**. Do not use the Upload block for video.

- [ ] Every video in the course is on YouTube and set to **Unlisted**, and was added to the
      lesson by pasting its YouTube link (see "How to add a video" below). No video was
      uploaded through the Upload block.
- [ ] Every video has captions that Caladrius has **reviewed or uploaded**. YouTube's
      automatic captions are not enough on their own: they get names, clinical terms and
      accents wrong, so read them through, or upload a corrected caption file.
- [ ] You played each video inside the lesson itself (not on YouTube) and saw the captions
      appear on screen. If you cannot see captions there, the course is not ready.
- [ ] No sample or demo videos are left in the course. The three videos in the demo course
      have no captions and must not be used.

**Limits you should know about**
- Learners **cannot switch captions on or off** in our player. They appear only if the
  video has captions and YouTube shows them by default. That is why you check them in the
  lesson (third item above).
- Nothing stops a video without captions from being published. This checklist is the only
  check.
- Videos you upload directly cannot have captions at all. That is the reason for the rule.

### How to add a video to a lesson

**First, in YouTube** (the wording in YouTube may change; use its own help if a menu has moved):
1. Upload the video to YouTube and set its visibility to **Unlisted**. Never leave it
   Public.
2. Make sure **embedding is allowed** for the video (the "Allow embedding" setting in the
   video's details in YouTube Studio). If it is off, the video will not play in the lesson.
3. Add and check the captions (see the checklist above).

**Then, in the course:**
1. Open the course, choose the **Course editor** tab, and pick the lesson in the chapter
   list on the right. To make a new one, use **Add Lesson**.
2. Click on an empty line in the lesson. To get one, click at the end of the existing
   content and press **Enter**.
3. **Paste the video's normal YouTube address** (the one from the browser's address bar,
   for example `https://www.youtube.com/watch?v=...`). It turns into the video player on its
   own.
4. Press play on it inside the lesson and check that the captions show (checklist item
   above).

**Things that are easy to get wrong**
- **There is no "video" button.** The "+" menu offers Text, Heading, List, Upload, Table,
  Quiz, Assignment, Programming Exercise, Markdown and CodeBox. Pasting the link is the way
  to add a video. **Do not use Upload for video.**
- **Changes save automatically.** There is no Save step: what you paste is saved to the
  lesson within seconds, so do not paste test links into a live course. Practise in a course
  that is not published.
- **Only YouTube has been tried.** The editor also recognises Vimeo, Cloudflare Stream and
  Bunny Stream links, but those are not covered by this guide or the captions rule.

## 2. Images: a description for every image

**The rule:** every image has a short description for people who cannot see it, or is
marked as decorative.

- [ ] Every image that carries information has a description that says what it shows and
      why it matters to the lesson (for example "Diagram of the eight phases of EMDR",
      not "image1.png" or "diagram").
- [ ] Images that are only decoration (borders, mood photos, repeated logos) are marked
      **Decorative** so a screen reader skips them.
- [ ] Text inside an image (a slide, a chart) is also written out in the lesson text.

**Limits**
- The platform lets you set a description but does not make you. An image can still be
  saved with none.
- Images added before this feature existed have no description until someone edits them.
  An administrator can list those with the image description audit
  (`bench --site <site> execute lms.lms.image_alt_audit.audit`).

## 3. Before you submit for review

- [ ] I went through sections 1 and 2 for every lesson, not only the first.
- [ ] I opened the lesson as a learner and played every video.
- [ ] I read the course description and quiz questions: any images there have descriptions too.

## 4. Reviewer sign-off

Complete this on a copy or in the review ticket. Do not publish until every line is ticked.

| | |
|---|---|
| Course | |
| Reviewer | |
| Date | |
| Lessons checked (number of lessons / number with video / number with images) | |
| Videos played in the lesson with captions visible | Yes / No |
| Every informative image has a description, decorative ones are marked | Yes / No |
| Notes or fixes needed | |
| Approved to publish | Yes / No |

## Certificate: CE hours (optional)

If a course carries continuing education (CE) hours, enter them so they print on the certificate.

1. Open the course and go to the **Settings** tab, then **Pricing and certification**.
2. Turn on **Completion certificate** (or **Paid certificate**). The **CE hours** box appears
   under the switches.
3. Type the number of hours, for example `6` or `1.5`. Changes save automatically.

Leave it empty if the course carries no CE hours: the certificate then simply leaves that figure
out, and nothing else changes.

**Limits you should know about**
- **Each certificate keeps the CE hours the course had on the day it was issued.** Changing
  the course's CE hours later does not change certificates already issued, only the ones issued
  from then on. Set the number *before* anyone completes the course.
- **Certificates issued before this existed print no CE hours**, even if the course now has some.
- **A recorded figure is locked.** If a certificate was issued with the wrong number, it cannot be
  edited; it has to be corrected by a developer or the certificate reissued.
- Only the number of hours is stored and printed. Nothing checks that it is correct or matches
  what EMDRIA approved for the course.
- **The signature line is blank for now.** Each certificate carries a line for the company's
  signature with Jessie Ogienko's name and title (Chief Executive Officer) beneath it, next to the
  instructor's name. Her signature image has not been added yet, so until it is the line is
  empty. Adding it is a small change a developer makes in the certificate template.
- The certificate does not yet print an EMDRIA approved provider statement or number. That
  needs the exact wording and number from you.

## What this does not cover yet

- The "How to add a video" steps were checked on a test copy with one browser. They have not
  been tried on a phone, in Safari, or with an unlisted video.
- Learners using a screen reader have not been tested on the video player: this is part of
  the screen-reader testing still to be done (issue #35).
- Audio lessons, quiz, assignment and PDF handout accessibility are not part of this
  checklist. EMDRIA's stated requirements are about video captions and image
  descriptions, and those are what this covers.
- The platform has no automatic enforcement. If you want publishing blocked until captions
  and image descriptions exist, that is development work, not a setting.
