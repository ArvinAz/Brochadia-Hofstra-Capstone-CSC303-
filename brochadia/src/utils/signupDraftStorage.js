const SIGNUP_DRAFT_STORAGE_KEY = 'brochadiaSignupDraft'

export function getSignupDraft() {
  const rawDraft = window.sessionStorage.getItem(SIGNUP_DRAFT_STORAGE_KEY)
  if (!rawDraft) return null

  try {
    return JSON.parse(rawDraft)
  } catch {
    return null
  }
}

export function storeSignupDraft(signupDraft) {
  window.sessionStorage.setItem(
    SIGNUP_DRAFT_STORAGE_KEY,
    JSON.stringify(signupDraft),
  )
}

export function clearSignupDraft() {
  window.sessionStorage.removeItem(SIGNUP_DRAFT_STORAGE_KEY)
}
