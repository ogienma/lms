<template>
	<PageHeader :breadcrumbs="breadcrumbs" />
	<div class="data-import-host">
		<DataImportWizard
			:dataImport="dataImport"
			@open-list="openList"
			@open-record="openRecord"
			@open-imports="openImports"
			@new-import="newImport"
		/>
	</div>
</template>
<script setup lang="ts">
import { usePageMeta } from 'frappe-ui'
import {
	DataImportWizard,
	useDataImport,
} from '@framework/ui/components/DataImport/index'
import PageHeader from '@/components/Layouts/pages/PageHeader.vue'
import type { Breadcrumb } from '@/types'
import { sessionStore } from '../stores/session'
import { useRoute, useRouter } from 'vue-router'
import { computed, inject, onMounted, ref, watch } from 'vue'

const { brand } = sessionStore()
const route = useRoute()
const router = useRouter()
const user = inject<any>('$user')

// Both route segments are single dynamic params (routes.js), never repeated —
// narrowed here because vue-router types every param as `string | string[]`.
const doctypeParam = computed(() =>
	Array.isArray(route.params.doctype)
		? route.params.doctype[0]
		: route.params.doctype
)
const importNameParam = computed(() =>
	Array.isArray(route.params.importName)
		? route.params.importName[0]
		: route.params.importName
)

onMounted(() => {
	if (!user.data?.is_moderator) {
		router.push({
			name: 'Courses',
		})
	}
})

// The wizard has no router of its own: the app owns the import's name and the
// links out of it. A new import has no name until it is first saved.
const name = ref<string | null>(importNameParam.value ?? null)
const dataImport = useDataImport(name, { doctype: () => doctypeParam.value })

// Keep the address in step with the import: it gains a name when first saved,
// and the address changing (a link in the app) opens another import.
watch(name, (next) => {
	if (next && next !== importNameParam.value) {
		router.replace({ name: 'DataImport', params: { importName: next } })
	}
})
watch(importNameParam, (next) => {
	if ((next ?? null) !== name.value) name.value = next ?? null
})

const listRoutes: Record<string, string> = {
	'LMS Course': '/courses',
	'LMS Batch': '/batches',
	'LMS Category': '/lms',
}

const openList = (doctype: string) => {
	router.push(listRoutes[doctype] || '/courses')
}

// Only courses have a page of their own to open.
const openRecord = (doctype: string, docname: string) => {
	if (doctype === 'LMS Course') router.push(`/courses/${docname}`)
}

// The app has no list of Data Import records, so "Review pending imports" goes
// to the one in the desk.
const openImports = (doctype: string) => {
	const filters = new URLSearchParams({
		reference_doctype: doctype,
		status: 'Pending',
	})
	window.location.href = `/desk/data-import?${filters}`
}

const newImport = (doctype: string) => {
	name.value = null
	router.push({ name: 'NewDataImport', params: { doctype } })
}

// Named here rather than taken from the imported component: its own trail is
// internal state we cannot reach, and the page still needs a back link on a
// phone.
const breadcrumbs = computed<Breadcrumb[]>(() => {
	const crumbs: Breadcrumb[] = [
		{ label: __('Data Import'), route: { name: 'DataImportList' } },
	]
	if (route.params.importName) crumbs.push({ label: __('Import') })
	else if (route.params.doctype)
		crumbs.push({ label: String(route.params.doctype) })
	return crumbs
})

usePageMeta(() => {
	return {
		title: __('Data Import'),
		icon: brand.favicon,
	}
})
</script>

<style scoped>
/* The wizard fills its parent's height, so give it the room under the header. */
.data-import-host {
	display: flex;
	min-height: 0;
	flex: 1 1 0;
	flex-direction: column;
}
</style>
