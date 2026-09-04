export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
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
