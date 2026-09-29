import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sessionStore } from './session'

export const useSidebar = defineStore('sidebar', () => {
	const { isLoggedIn } = sessionStore()

	// A guest is offered two or three destinations, so the 224px sidebar is mostly
	// empty space: start them on the 56px icon rail. Only the toggle ever writes
	// to localStorage, so a visitor who never chose keeps the default for their
	// role, and gets the full sidebar once they sign in.
	const isSidebarCollapsed = ref(!isLoggedIn.value)
	const isWebpagesCollapsed = ref(true)

	if (localStorage.getItem('isSidebarCollapsed')) {
		isSidebarCollapsed.value = JSON.parse(
			localStorage.getItem('isSidebarCollapsed')
		)
	}

	if (localStorage.getItem('isWebpagesCollapsed')) {
		isWebpagesCollapsed.value = JSON.parse(
			localStorage.getItem('isWebpagesCollapsed')
		)
	}

	return {
		isSidebarCollapsed,
		isWebpagesCollapsed,
	}
})
