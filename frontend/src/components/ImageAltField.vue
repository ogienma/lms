<template>
	<div
		v-if="image"
		class="flex items-center gap-2 rounded-b-5 border border-t-0 border-outline-elevation-2 bg-surface-elevation-1 p-2"
	>
		<label :for="inputId" class="shrink-0 text-xs text-ink-gray-7">
			{{ __('Image description') }}
		</label>
		<input
			:id="inputId"
			type="text"
			:value="image.alt"
			:disabled="image.decorative"
			:placeholder="__('Describe the image for screen readers')"
			class="min-w-0 flex-1 rounded-5 border border-outline-elevation-2 bg-surface-base px-2 py-1 text-sm text-ink-gray-9 disabled:opacity-50"
			@input="setAlt(($event.target as HTMLInputElement).value)"
		/>
		<Checkbox
			size="md"
			:label="__('Decorative')"
			:model-value="image.decorative"
			@update:model-value="setDecorative(!!$event)"
		/>
	</div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { Checkbox } from 'frappe-ui'
import type { Editor } from '@tiptap/vue-3'

/**
 * Alt text for the selected image in a rich-text field. The frappe-ui image
 * node keeps an `alt` attribute, but only its multi-image dialog offers a
 * field, and that one is a caption. Selecting an image shows this row.
 *
 * "Decorative" is stored as `alt=""`: an image the author deliberately marked,
 * as opposed to one nobody described (alt null).
 */
const props = defineProps<{ editor?: Editor | null }>()

const inputId = `image-alt-${Math.random().toString(36).slice(2)}`
const image = ref<{ alt: string; decorative: boolean } | null>(null)

function sync() {
	const editor = props.editor
	if (!editor || !editor.isEditable || !editor.isActive('image')) {
		image.value = null
		return
	}
	const alt = editor.getAttributes('image').alt
	image.value = { alt: alt ?? '', decorative: alt === '' }
}

// An emptied field is null, not '': '' means "decorative" and would flip the
// checkbox and disable the field under the author's cursor.
function setAlt(alt: string) {
	props.editor
		?.chain()
		.updateAttributes('image', { alt: alt || null })
		.run()
}

function setDecorative(on: boolean) {
	props.editor
		?.chain()
		.updateAttributes('image', { alt: on ? '' : null })
		.run()
}

let bound: Editor | null = null
function bind(editor?: Editor | null) {
	bound?.off('transaction', sync)
	bound = editor ?? null
	bound?.on('transaction', sync)
	sync()
}

watch(() => props.editor, bind, { immediate: true })
onBeforeUnmount(() => bind(null))
</script>
