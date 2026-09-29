import frappeUIPreset from 'frappe-ui/tailwind'
import { safeAreaPlugin } from './tailwind/safeArea.js'

export default {
	presets: [frappeUIPreset],
	content: [
		'./index.html',
		'./src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
		'../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
		'./node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
		'../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
	],
	theme: {
		extend: {
			// Archivo is the brand/UI face; Atkinson Hyperlegible Next is for text
			// people read at length. Stacks live in public/css/fonts.css.
			fontFamily: {
				sans: 'var(--font-ui)',
				reading: 'var(--font-reading)',
			},
			strokeWidth: {
				1.5: '1.5',
			},
			screens: {
				'2xl': '1600px',
				'3xl': '1920px',
			},
		},
	},
	plugins: [safeAreaPlugin],
}
