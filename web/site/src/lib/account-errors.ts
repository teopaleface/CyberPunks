/** Translate account errors for display without changing requests or authentication rules. */
const ACCOUNT_ERRORS: Record<string, string> = {
  "Adresa de email nu pare corectă.": "Enter a valid email address.",
  "Parola trebuie să aibă cel puțin 6 caractere.": "Use a password with at least 6 characters.",
  "Există deja un cont cu acest email. Intră în cont.": "An account already exists for this email. Sign in instead.",
  "Emailul sau parola nu se potrivesc. Verifică-le și încearcă din nou.": "The email or password is incorrect. Check them and try again.",
  "Intră în cont ca să îți salvezi profilul.": "Sign in to save your profile.",
  "Intră în cont ca să schimbi parola.": "Sign in to change your password.",
  "Lipsește legătura KV CONTURI (wrangler.jsonc).": "Accounts are unavailable on this server. Try again later.",
  "Ceva n-a mers. Încearcă din nou.": "Something went wrong. Try again.",
  "Nu ne-am putut conecta la server. Verifică internetul și încearcă din nou.": "Could not connect to the server. Check your connection and try again.",
}

export function accountErrorMessage(error: string): string {
  return ACCOUNT_ERRORS[error] ?? "The account request failed. Check your details and try again."
}
