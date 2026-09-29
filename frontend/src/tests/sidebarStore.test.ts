/**
 * The sidebar's starting width.
 *
 * A guest is offered two or three destinations, so the full sidebar is mostly
 * empty space and they start on the icon rail; a signed-in user keeps the full
 * one. What is pinned here is the precedence: an explicit choice — the toggle
 * writes one to localStorage — outranks either default, in both directions, so
 * a guest who expanded the sidebar is not collapsed again on the next visit and
 * a member who collapsed it is not re-expanded.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ref } from 'vue'

const { session } = vi.hoisted(() => ({
	session: { isLoggedIn: undefined as unknown },
}))

vi.mock('@/stores/session', () => ({ sessionStore: () => session }))

import { useSidebar } from '@/stores/sidebar'

const visitAs = (loggedIn: boolean) => {
	session.isLoggedIn = ref(loggedIn)
}

beforeEach(() => {
	localStorage.clear()
	setActivePinia(createPinia())
})

describe('useSidebar default', () => {
	it('starts a guest on the icon rail', () => {
		visitAs(false)
		expect(useSidebar().isSidebarCollapsed).toBe(true)
	})

	it('leaves a signed-in user on the full sidebar', () => {
		visitAs(true)
		expect(useSidebar().isSidebarCollapsed).toBe(false)
	})
})

describe('useSidebar stored choice', () => {
	it('keeps a guest who expanded it expanded', () => {
		visitAs(false)
		localStorage.setItem('isSidebarCollapsed', 'false')
		expect(useSidebar().isSidebarCollapsed).toBe(false)
	})

	it('keeps a signed-in user who collapsed it collapsed', () => {
		visitAs(true)
		localStorage.setItem('isSidebarCollapsed', 'true')
		expect(useSidebar().isSidebarCollapsed).toBe(true)
	})
})
