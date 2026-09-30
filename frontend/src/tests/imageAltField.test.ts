import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ImageAltField from '@/components/ImageAltField.vue'

// Just enough of a TipTap editor: the selected image's attrs, the update chain,
// and transaction listeners.
const makeEditor = (attrs: Record<string, unknown> | null) => {
	const listeners = new Set<() => void>()
	const run = vi.fn()
	const updateAttributes = vi.fn(() => ({ run }))
	return {
		isEditable: true,
		isActive: (name: string) => name === 'image' && attrs !== null,
		getAttributes: () => attrs ?? {},
		chain: () => ({ updateAttributes }),
		on: (_: string, fn: () => void) => listeners.add(fn),
		off: (_: string, fn: () => void) => listeners.delete(fn),
		updateAttributes,
		fire: () => listeners.forEach((fn) => fn()),
	}
}

const mountWith = (editor: ReturnType<typeof makeEditor>) =>
	mount(ImageAltField, {
		props: { editor: editor as never },
		global: { mocks: { __: (s: string) => s } },
	})

describe('ImageAltField', () => {
	it('is hidden unless an image is selected', () => {
		expect(mountWith(makeEditor(null)).find('input').exists()).toBe(false)
	})

	it('shows the selected image alt', () => {
		const w = mountWith(makeEditor({ alt: 'A cat' }))
		expect((w.find('input[type=text]').element as HTMLInputElement).value).toBe(
			'A cat'
		)
	})

	it('writes typed text to the image node', async () => {
		const editor = makeEditor({ alt: null })
		const w = mountWith(editor)
		await w.find('input[type=text]').setValue('A dog')
		expect(editor.updateAttributes).toHaveBeenCalledWith('image', {
			alt: 'A dog',
		})
	})

	it('stores an emptied field as null, never as decorative', async () => {
		const editor = makeEditor({ alt: 'A dog' })
		const w = mountWith(editor)
		await w.find('input[type=text]').setValue('')
		expect(editor.updateAttributes).toHaveBeenCalledWith('image', { alt: null })
	})

	it('marks an image decorative with an empty alt and disables the field', async () => {
		const editor = makeEditor({ alt: null })
		const w = mountWith(editor)
		await w.find('input[type=checkbox]').setValue(true)
		expect(editor.updateAttributes).toHaveBeenCalledWith('image', { alt: '' })

		const deco = mountWith(makeEditor({ alt: '' }))
		expect(
			(deco.find('input[type=checkbox]').element as HTMLInputElement).checked
		).toBe(true)
		expect(
			(deco.find('input[type=text]').element as HTMLInputElement).disabled
		).toBe(true)
	})
})
