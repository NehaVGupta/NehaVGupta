export const passwordRequirements = (password) => [
	['At least 8 characters', password.length >= 8],
	['Uppercase letter', /[A-Z]/.test(password)],
	['Lowercase letter', /[a-z]/.test(password)],
	['Number', /[0-9]/.test(password)],
	['Special character', /[^A-Za-z0-9]/.test(password)],
]