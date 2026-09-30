import { describe, expect, it } from 'vitest'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'

// EMDRIA #36: frappe-ui draws the keyboard focus ring globally on :focus-visible,
// so `outline-none` on an element deletes it. A line that suppresses the outline
// must either carry its own visible replacement, or be a programmatic focus
// target (a tabindex="-1" region) listed below.

const SRC = resolve(__dirname, '..')
const REPLACEMENT =
	/focus(-visible)?:ring-2|focus(-visible)?:ring-outline|focus-visible:focus-ring|focus(-visible|-within)?:border-outline|focus-within:/

// Regions the app moves focus to (skip link, route change, form hand-back).
const PROGRAMMATIC_TARGETS = new Set([
	'components/Layouts/MobileLayout.vue',
	'components/Layouts/NoSidebarLayout.vue',
	'components/Layouts/DesktopLayout.vue',
	'components/Persona/PersonaCard.vue',
	// The outline is removed here, but the visible replacement (a border change
	// and shadow) lives on a wrapper or a sibling class string: reviewed by hand.
	'components/Controls/Link.vue',
	'components/Controls/MultiLink.vue',
	'components/Controls/MultiSelect.vue',
	'components/Courses/CourseOverviewSection.vue',
	'pages/Batches/BatchForm.vue',
	'pages/Forms/NewBatchForm.vue',
])

const vueFiles = (dir: string): string[] =>
	readdirSync(dir).flatMap((name) => {
		const path = join(dir, name)
		if (statSync(path).isDirectory()) {
			return name === 'tests' ? [] : vueFiles(path)
		}
		return path.endsWith('.vue') ? [path] : []
	})

describe('focus indicators', () => {
	it('no element removes its outline without a visible replacement', () => {
		const offenders: string[] = []
		for (const file of vueFiles(SRC)) {
			const rel = relative(SRC, file).replaceAll('\\', '/')
			if (PROGRAMMATIC_TARGETS.has(rel)) continue
			readFileSync(file, 'utf8')
				.split('\n')
				.forEach((line, i) => {
					const removesOutline = /(^|[\s'"])(focus(-visible)?:)?outline-none/.test(line)
					if (removesOutline && !REPLACEMENT.test(line)) {
						offenders.push(`${rel}:${i + 1}`)
					}
				})
		}
		expect(offenders).toEqual([])
	})
})
