const USER_ID_STORAGE_KEY = 'brochadiaUserId'

export function getStoredUserId() {
  return window.localStorage.getItem(USER_ID_STORAGE_KEY)
}

export function storeUserId(userId) {
  window.localStorage.setItem(USER_ID_STORAGE_KEY, userId)
  console.log('Saved MongoDB user id:', window.localStorage.getItem(USER_ID_STORAGE_KEY))
}

export function clearStoredUserId() {
  window.localStorage.removeItem(USER_ID_STORAGE_KEY)
}
