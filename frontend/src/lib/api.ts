export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const CACHE_TTL_MINUTES = 40;
const CACHE_PREFIX = "vayu-cache:";

function cacheKey(path: string) {
  return `${CACHE_PREFIX}${path}`;
}

export function readCachedData<T>(path: string, ttlMinutes = CACHE_TTL_MINUTES): T | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(cacheKey(path));
    if (!raw) return null;
    const cached = JSON.parse(raw) as { timestamp: number; data: T } | null;
    if (!cached || typeof cached.timestamp !== "number") return null;
    const ageMinutes = (Date.now() - cached.timestamp) / (60 * 1000);
    if (ageMinutes > ttlMinutes) {
      window.localStorage.removeItem(cacheKey(path));
      return null;
    }
    return cached.data;
  } catch {
    try {
      window.localStorage.removeItem(cacheKey(path));
    } catch {}
    return null;
  }
}

export async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

export async function getCached<T>(path: string, ttlMinutes = CACHE_TTL_MINUTES, forceRefresh = false): Promise<T> {
  if (!forceRefresh && typeof window !== "undefined") {
    const cached = readCachedData<T>(path, ttlMinutes);
    if (cached !== null) return cached;
  }

  const data = await get<T>(path);

  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(cacheKey(path), JSON.stringify({ timestamp: Date.now(), data }));
    } catch {
      // ignore storage quota issues gracefully
    }
  }

  return data;
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 1 }).format(value);
}

export function formatMoney(value: number) {
  return `₹${new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(value)}`;
}

export function formatPercent(value: number | null | undefined) {
  return `${value !== null && value !== undefined && value >= 0 ? "+" : ""}${(value || 0).toFixed(1)}%`;
}
