export type Role = "investor" | "startup";

const KEY = "vcbrain_role";

export function loadRole(): Role | null {
  const saved = localStorage.getItem(KEY);
  return saved === "investor" || saved === "startup" ? saved : null;
}

export function saveRole(role: Role) {
  localStorage.setItem(KEY, role);
}

export function clearRole() {
  localStorage.removeItem(KEY);
}
