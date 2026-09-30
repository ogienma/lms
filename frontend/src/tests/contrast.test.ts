import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import postcss from 'postcss'
import colors from '../../node_modules/frappe-ui/tailwind/generated/colors.json'

// EMDRIA #36: WCAG AA. Ratios are computed from the values index.css actually
// declares (overrides) layered over frappe-ui's own token data, so an upstream
// palette change, or an edit here that drops below the minimum, fails this suite.

type Theme = 'light' | 'dark'
const palette = colors as any

const resolveRef = (ref: string): string => {
	if (ref.startsWith('neutral/')) return palette.neutral[ref.split('/')[1]]
	const [group, name, shade] = ref.split('/')
	return palette[group][name][shade]
}

const overrides = (theme: Theme): Record<string, string> => {
	const css = readFileSync(resolve(__dirname, '../index.css'), 'utf8')
	const wanted = theme === 'light' ? ':root' : "[data-theme='dark']"
	const out: Record<string, string> = {}
	postcss.parse(css).walkRules((rule) => {
		if (rule.selector !== wanted) return
		rule.walkDecls(/^--/, (d) => void (out[d.prop] = d.value))
	})
	return out
}

const token = (theme: Theme, category: string, name: string): string => {
	const own = overrides(theme)[`--${category}-${name}`]
	if (own) return own
	return resolveRef(palette.themedVariables[theme][category][name])
}

const luminance = (hex: string): number => {
	const h = hex.replace('#', '')
	const [r, g, b] = [0, 2, 4].map((i) => {
		const v = parseInt(h.slice(i, i + 2), 16) / 255
		return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
	})
	return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

const ratio = (a: string, b: string): number => {
	const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
	return (hi + 0.05) / (lo + 0.05)
}

// The page, then the fills that inputs, cards and hover rows sit on.
const TEXT_SURFACES: Record<Theme, string[]> = {
	light: ['base', 'gray-1', 'gray-2', 'gray-3'],
	dark: ['base', 'gray-1', 'gray-2'],
}

describe.each(['light', 'dark'] as Theme[])('%s theme contrast', (theme) => {
	for (const ink of ['gray-4', 'gray-5', 'gray-6', 'gray-7']) {
		it(`ink-${ink} reaches 4.5:1 on every text surface`, () => {
			for (const surface of TEXT_SURFACES[theme]) {
				expect(
					ratio(token(theme, 'ink', ink), token(theme, 'surface', surface)),
					`ink-${ink} on surface-${surface}`,
				).toBeGreaterThanOrEqual(4.5)
			}
		})
	}

	it('keeps the emphasis order gray-4 <= gray-5 <= gray-6', () => {
		const page = token(theme, 'surface', 'base')
		const emphasis = (n: string) => ratio(token(theme, 'ink', n), page)
		expect(emphasis('gray-4')).toBeLessThanOrEqual(emphasis('gray-5') + 0.01)
		expect(emphasis('gray-5')).toBeLessThanOrEqual(emphasis('gray-6') + 0.01)
	})

	it('default keyboard focus ring reaches 3:1 against the page', () => {
		const ring = overrides(theme)['--focus-outline-default']
		const hex = ring?.match(/#[0-9a-f]{6}/i)?.[0]
		expect(hex, 'index.css must declare --focus-outline-default').toBeTruthy()
		expect(
			ratio(hex!, token(theme, 'surface', 'base')),
		).toBeGreaterThanOrEqual(3)
	})

	for (const name of ['gray-4', 'gray-5']) {
		it(`outline-${name} (focus borders and rings) reaches 3:1`, () => {
			expect(
				ratio(token(theme, 'outline', name), token(theme, 'surface', 'base')),
			).toBeGreaterThanOrEqual(3)
		})
	}
})

describe('primary button', () => {
	it('brand text on salmon reaches 4.5:1 in every state', () => {
		for (const bg of ['#f8c4b7', '#f5b3a3', '#f0a08d']) {
			expect(ratio('#3c210e', bg)).toBeGreaterThanOrEqual(4.5)
		}
	})
})
