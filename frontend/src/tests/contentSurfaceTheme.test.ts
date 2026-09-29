import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import postcss from 'postcss'

// Lessons and PDF handouts painted themselves from colours that ignore
// data-theme: PdfBlock used the fixed --gray-* scale (gray-50 is near-white in
// dark mode) and Lesson.vue pinned code blocks to hex editor themes. Both now
// read themed tokens; these checks keep a fixed colour from creeping back.

const ROOT = resolve(__dirname, '../..')
const read = (path: string) => readFileSync(resolve(ROOT, path), 'utf8')

const styleBlocks = (sfc: string): string =>
	[...sfc.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)]
		.map((m) => m[1])
		.join('\n')

const CODE_VARS = [
	'--code-bg',
	'--code-fg',
	'--code-comment',
	'--code-keyword',
	'--code-name',
	'--code-literal',
	'--code-string',
	'--code-number',
	'--code-title',
	'--code-built-in',
]

const declaredIn = (selector: string): Set<string> => {
	const found = new Set<string>()
	postcss.parse(read('src/index.css')).walkRules((rule) => {
		if (!rule.selectors.some((s) => s.trim() === selector)) return
		rule.walkDecls((decl) => found.add(decl.prop))
	})
	return found
}

describe('content surfaces follow the app theme', () => {
	it('PdfBlock chrome uses no fixed --gray-*/--blue-*/--white scale', () => {
		const css = styleBlocks(read('src/components/PdfBlock.vue'))
		expect(css).not.toMatch(/var\(--(gray|blue|white)\b/)
	})

	it('Lesson.vue styles pin no hex or fixed Tailwind colours', () => {
		const css = styleBlocks(read('src/pages/Lesson.vue'))
		expect(css).not.toMatch(/theme\(['"]colors\./)
		expect(css).not.toMatch(/#[0-9a-fA-F]{3,8}\b/)
	})

	it('CodeBox token palette reads the --code-* variables only', () => {
		const code = read('src/utils/code.ts')
		const palette = code.match(/CODEBOX_THEME_CSS = `([\s\S]*?)`/)?.[1] ?? ''
		expect(palette).toContain('var(--code-fg)')
		expect(palette).not.toMatch(/#[0-9a-fA-F]{3,8}\b/)
	})

	it.each([':root', "[data-theme='dark']"])(
		'declares every --code-* variable under %s',
		(selector) => {
			const declared = declaredIn(selector)
			for (const name of CODE_VARS) expect(declared).toContain(name)
		}
	)
})
