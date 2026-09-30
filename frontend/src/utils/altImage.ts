// @ts-ignore -- @editorjs/simple-image ships no type declarations
import SimpleImage from '@editorjs/simple-image'

/**
 * SimpleImage with alternative text. The stock tool saves only url, caption and
 * the style flags and renders a bare `<img>`, so a lesson image has no `alt`
 * for a screen reader (EMDRIA: every image carries meaningful alt text).
 *
 * `alt` describes the image. `decorative` marks one that adds nothing for a
 * screen reader; it renders `alt=''`, which is the correct way to say so. The
 * caption stays the visible text and is not reused as alt: a caption the
 * author wrote for sighted readers is not a description, and the stock drop
 * handler fills it with the file name.
 */
export class AltImage extends (SimpleImage as any) {
	altInput: HTMLInputElement | null = null

	constructor(options: any) {
		super(options)
		const { alt, decorative } = options.data || {}
		this.data = { alt: alt || '', decorative: !!decorative }
		this.tunes.push({
			name: 'decorative',
			label: 'Decorative image (no alt text)',
			icon: DECORATIVE_ICON,
		})
	}

	render(): HTMLElement {
		const wrapper: HTMLElement = super.render()
		this.altInput = this._make('input', [this.CSS.input, 'cdx-simple-image__alt'], {
			value: this.data.alt,
			placeholder: this.api.i18n.t('Describe the image for screen readers'),
			disabled: this.readOnly || this.data.decorative,
		}) as HTMLInputElement
		this.altInput.setAttribute('aria-label', 'Image alt text')
		this.altInput.addEventListener('input', () => {
			this.data.alt = this.altInput!.value
			this._applyAlt()
		})
		// Parent appends the image holder and caption once the image loads;
		// the alt field goes in now so it never appears after them.
		if (!this.readOnly) wrapper.appendChild(this.altInput)
		this._applyAlt()
		return wrapper
	}

	save(blockContent: HTMLElement) {
		return {
			...super.save(blockContent),
			alt: this.data.decorative ? '' : this.data.alt,
			decorative: !!this.data.decorative,
		}
	}

	static get sanitize() {
		return { ...(SimpleImage as any).sanitize, alt: {}, decorative: {} }
	}

	_toggleTune(name: string) {
		super._toggleTune(name)
		if (name === 'decorative' && this.altInput) {
			this.altInput.disabled = !!this.data.decorative
		}
		this._applyAlt()
	}

	_applyAlt() {
		if (this.nodes.image) {
			this.nodes.image.alt = this.data.decorative ? '' : this.data.alt || ''
		}
	}
}

const DECORATIVE_ICON =
	`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24"><path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="M5 19L19 5M7 7h10v10H7z"/></svg>`
