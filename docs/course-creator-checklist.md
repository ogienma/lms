# Course creator checklist: accessibility and EMDRIA

Use this before you publish a course, and again for the review. It covers what the
platform cannot check for you. Anything not ticked means the course is not ready.

Why these rules exist: EMDRIA requires that video has closed captions and that every
image has alternative text. The platform does not enforce either one, so this checklist
is the safeguard. (Tracked in issues #37 and #34.)

## 1. Video: captions are required

**The rule:** all lesson video is hosted on **YouTube, set to Unlisted**, and has
**accurate captions**. Do not use the Upload block for video.

- [ ] Every video in the course is on YouTube and set to **Unlisted**, and added to the
      lesson as a YouTube/Video Hosting block. No video was uploaded through the Upload block.
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

## What this does not cover yet

- Learners using a screen reader have not been tested on the video player: this is part of
  the screen-reader testing still to be done (issue #35).
- Audio lessons, quiz, assignment and PDF handout accessibility are not part of this
  checklist. EMDRIA's stated requirements are about video captions and image
  descriptions, and those are what this covers.
- The platform has no automatic enforcement. If you want publishing blocked until captions
  and image descriptions exist, that is development work, not a setting.
