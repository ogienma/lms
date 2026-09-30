import { describe, expect, it } from 'vitest'
import { AltImage } from '@/utils/altImage'

const api = {
	styles: { block: 'b', loader: 'l', input: 'i' },
	blocks: { getCurrentBlockIndex: () => 0, stretchBlock: () => {} },
	i18n: { t: (s: string) => s },
}

const make = (data: object, readOnly = false) => {
	const tool = new AltImage({ data, config: {}, api, readOnly })
	const el = tool.render() as HTMLElement
	// The tool attaches the img only once it loads; jsdom never loads it.
	tool.nodes.image.onload()
	return { tool, el }
}

describe('AltImage', () => {
	it('renders the saved alt on the img', () => {
		const { el } = make({ url: '/a.png', alt: 'A cat' }, true)
		expect(el.querySelector('img')!.getAttribute('alt')).toBe('A cat')
	})

	it('always sets an alt attribute, even when none was saved', () => {
		const { el } = make({ url: '/a.png' }, true)
		expect(el.querySelector('img')!.hasAttribute('alt')).toBe(true)
	})

	it('offers no alt field to readers', () => {
		const { el } = make({ url: '/a.png', alt: 'x' }, true)
		expect(el.querySelector('input')).toBeNull()
	})

	it('typing in the field updates the img and the saved data', () => {
		const { tool, el } = make({ url: '/a.png' })
		const input = el.querySelector('input')!
		input.value = 'A dog'
		input.dispatchEvent(new Event('input'))
		expect(el.querySelector('img')!.alt).toBe('A dog')
		expect(tool.save(el).alt).toBe('A dog')
	})

	it('decorative images save and render an empty alt', () => {
		const { tool, el } = make({ url: '/a.png', alt: 'x', decorative: true })
		expect(el.querySelector('img')!.alt).toBe('')
		expect(tool.save(el)).toMatchObject({ alt: '', decorative: true })
	})

	it('keeps alt through sanitizing', () => {
		expect(AltImage.sanitize).toHaveProperty('alt')
	})
})
