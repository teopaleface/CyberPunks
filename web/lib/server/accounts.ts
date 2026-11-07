import "server-only";
import { cookies } from "next/headers";
import { mayAddDemoRecovery, sameMembership } from "@/lib/operations/demo-permissions";
import { membershipOf, unboundCustomer, type Membership } from "@/lib/operations/policy";

/**
 * Conturile site-ului (/intra) și aprobările lor, în Cloudflare KV (legătura CONTURI; local, KV-ul simulat de
 * wrangler prin initOpenNextCloudflareForDev). Fără Supabase și fără confirmare pe email (decizia lui Teo).
 * Chei: u:email:<email> → id; u:<id> → utilizatorul; s:<sha256(token)> → id (30 de zile); a:<id> → aprobările.
 */

export interface KV {
  get(key: string): Promise<string | null>;
  put(key: string, value: string, opts?: { expirationTtl?: number }): Promise<void>;
  delete(key: string): Promise<void>;
}

export interface StoredUser {
  id: string;
  email: string;
  full_name: string | null;
  team: string | null;
  salt: string;
  hash: string;
  iter: number;
  created_at: string;
  membership?: Membership;
  synthetic_demo?: boolean;
  capability_grants?: { permission: "recover_commands"; granted_at: string; source: "local_demo_provisioning"; credentials_verified: true }[];
}
export interface PublicUser {
  id: string;
  email: string;
}
export interface Profile {
  id: string;
  full_name: string | null;
  team: string | null;
}

export const COOKIE = process.env.DAYBREAK_COOKIE_NAME ?? "daybreak_sesiune";
const SESSION_DAYS = 30;
// iterațiile PBKDF2: puține cât să încapă în limita de procesor a planului gratuit Workers (10 ms)
const ITER = 10_000;

async function kv(): Promise<KV> {
  const { getCloudflareContext } = await import("@opennextjs/cloudflare");
  const { env } = await getCloudflareContext({ async: true });
  const store = (env as unknown as { CONTURI?: KV }).CONTURI;
  if (!store) throw new Error("Lipsește legătura KV CONTURI (wrangler.jsonc).");
  return store;
}

const enc = new TextEncoder();
const hex = (b: ArrayBuffer | Uint8Array) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
const randomHex = (n: number) => hex(crypto.getRandomValues(new Uint8Array(n)));
const sha256 = async (s: string) => hex(await crypto.subtle.digest("SHA-256", enc.encode(s)));

async function hashPassword(password: string, salt: string, iter = ITER): Promise<string> {
  const key = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: enc.encode(salt), iterations: iter }, key, 256);
  return hex(bits);
}

function sameText(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

const normEmail = (e: string) => e.trim().toLowerCase();
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const toPublic = (u: StoredUser): PublicUser => ({ id: u.id, email: u.email });
export const toProfile = (u: StoredUser): Profile => ({ id: u.id, full_name: u.full_name, team: u.team });

async function readUser(store: KV, id: string): Promise<StoredUser | null> {
  const raw = await store.get(`u:${id}`);
  return raw ? (JSON.parse(raw) as StoredUser) : null;
}

async function startSession(store: KV, userId: string): Promise<void> {
  const token = randomHex(32);
  await store.put(`s:${await sha256(token)}`, userId, { expirationTtl: SESSION_DAYS * 86400 });
  (await cookies()).set(COOKIE, token, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_DAYS * 86400,
  });
}

export async function currentUser(): Promise<StoredUser | null> {
  const token = (await cookies()).get(COOKIE)?.value;
  if (!token || !/^[0-9a-f]{64}$/.test(token)) return null;
  const store = await kv();
  const id = await store.get(`s:${await sha256(token)}`);
  return id ? readUser(store, id) : null;
}

export async function signUp(emailRaw: string, password: string, fullName: string): Promise<{ user?: StoredUser; error?: string }> {
  const email = normEmail(emailRaw);
  if (!EMAIL_RE.test(email)) return { error: "Adresa de email nu pare corectă." };
  if (password.length < 6) return { error: "Parola trebuie să aibă cel puțin 6 caractere." };
  const store = await kv();
  if (await store.get(`u:email:${email}`)) return { error: "Există deja un cont cu acest email. Intră în cont." };
  const salt = randomHex(16);
  const user: StoredUser = {
    id: crypto.randomUUID(),
    email,
    full_name: fullName.trim().slice(0, 120) || null,
    team: null,
    membership: unboundCustomer(),
    salt,
    hash: await hashPassword(password, salt),
    iter: ITER,
    created_at: new Date().toISOString(),
  };
  await store.put(`u:${user.id}`, JSON.stringify(user));
  await store.put(`u:email:${email}`, user.id);
  await startSession(store, user.id);
  return { user };
}

export async function signIn(emailRaw: string, password: string): Promise<{ user?: StoredUser; error?: string }> {
  const store = await kv();
  const id = await store.get(`u:email:${normEmail(emailRaw)}`);
  const user = id ? await readUser(store, id) : null;
  if (!user || !sameText(await hashPassword(password, user.salt, user.iter), user.hash)) {
    return { error: "Emailul sau parola nu se potrivesc. Verifică-le și încearcă din nou." };
  }
  await startSession(store, user.id);
  return { user };
}

export async function signOut(): Promise<void> {
  const jar = await cookies();
  const token = jar.get(COOKIE)?.value;
  if (token && /^[0-9a-f]{64}$/.test(token)) await (await kv()).delete(`s:${await sha256(token)}`);
  jar.delete(COOKIE);
}

export async function saveProfile(user: StoredUser, patch: { full_name?: string | null; team?: string | null }): Promise<StoredUser> {
  const next: StoredUser = {
    ...user,
    ...(patch.full_name !== undefined ? { full_name: patch.full_name?.trim().slice(0, 120) || null } : {}),
    ...(patch.team !== undefined ? { team: patch.team?.slice(0, 60) || null } : {}),
  };
  await (await kv()).put(`u:${user.id}`, JSON.stringify(next));
  return next;
}

export async function setPassword(user: StoredUser, password: string): Promise<string | null> {
  if (password.length < 6) return "Parola trebuie să aibă cel puțin 6 caractere.";
  const salt = randomHex(16);
  await (await kv()).put(`u:${user.id}`, JSON.stringify({ ...user, salt, hash: await hashPassword(password, salt), iter: ITER }));
  return null;
}

export type ApprovalRow = { post_id: string; decision: "approved" | "deferred" | "rejected"; crew_id: string | null };

export async function readApprovals(userId: string): Promise<ApprovalRow[]> {
  const raw = await (await kv()).get(`a:${userId}`);
  return raw ? (JSON.parse(raw) as ApprovalRow[]) : [];
}

export async function writeApprovals(userId: string, rows: ApprovalRow[]): Promise<void> {
  await (await kv()).put(`a:${userId}`, JSON.stringify(rows.slice(0, 2000)));
}

/** Profil sigur pentru aplicație; apartenența nu se editează prin profil. */
export const toMembership = (user: StoredUser) => membershipOf(user);

export interface DemoAccountInput { email: string; password: string; membership: Membership }
/** Numai ruta locală activată explicit. Păstrează identitățile și parolele; permite exclusiv extinderea sintetică recover_commands. */
export async function provisionDemoAccounts(inputs: DemoAccountInput[]) {
  return provisionDemoAccountsInStore(await kv(), inputs);
}

/** Procedura de stocare se testează fără acces la KV-ul real sau la cookie-uri. */
export async function provisionDemoAccountsInStore(store: KV, inputs: DemoAccountInput[]) {
  if (inputs.length !== 3 || new Set(inputs.map(x => x.membership.role)).size !== 3) throw new Error("Supply exactly three demo accounts.");
  const emails = inputs.map(x => normEmail(x.email));
  if (new Set(emails).size !== 3 || inputs.some((x, i) => !EMAIL_RE.test(emails[i]) || x.password.length < 12) || new Set(inputs.map(x => x.password)).size !== 3) throw new Error("Use three unique emails and independently supplied passwords of at least 12 characters.");
  const existingIds = await Promise.all(emails.map(email => store.get(`u:email:${email}`)));
  if (existingIds.some(Boolean)) {
    const existing = await Promise.all(existingIds.map(id => id ? readUser(store, id) : null));
    for (let i = 0; i < existing.length; i++) {
      const user = existing[i];
      if (!user || user.id !== existingIds[i] || user.email !== emails[i] || !user.synthetic_demo || (!sameMembership(user.membership, inputs[i].membership) && !mayAddDemoRecovery(user.membership, inputs[i].membership)) || !sameText(await hashPassword(inputs[i].password, user.salt, user.iter), user.hash)) throw new Error("An account already exists. Existing accounts are never overwritten.");
    }
    // Toate cele trei identități și parole au trecut verificarea înaintea oricărei scrieri.
    const upgraded = new Set<string>();
    for (let i = 0; i < existing.length; i++) {
      const user = existing[i]!;
      if (mayAddDemoRecovery(user.membership, inputs[i].membership)) {
        const next: StoredUser = { ...user, membership: { ...user.membership!, permissions: [...user.membership!.permissions, "recover_commands"] }, capability_grants: [...(user.capability_grants ?? []), { permission: "recover_commands", granted_at: new Date().toISOString(), source: "local_demo_provisioning", credentials_verified: true }] };
        await store.put(`u:${user.id}`, JSON.stringify(next));
        existing[i] = next;
        upgraded.add(user.id);
      }
    }
    return existing.map(u => ({ ...toPublic(u!), membership: toMembership(u!), synthetic: true, already_ready: true, ...(upgraded.has(u!.id) ? { membership_upgrade: { added_permissions: ["recover_commands"] } } : {}) }));
  }
  const users = await Promise.all(inputs.map(async (x, i): Promise<StoredUser> => {
    const salt = randomHex(16);
    return { id: crypto.randomUUID(), email: emails[i], full_name: `Demo ${x.membership.role}`, team: null, membership: x.membership, synthetic_demo: true, salt, hash: await hashPassword(x.password, salt), iter: ITER, created_at: new Date().toISOString() };
  }));
  for (const u of users) {
    await store.put(`u:${u.id}`, JSON.stringify(u));
    await store.put(`u:email:${u.email}`, u.id);
  }
  return users.map(u => ({ ...toPublic(u), membership: toMembership(u), synthetic: true }));
}
