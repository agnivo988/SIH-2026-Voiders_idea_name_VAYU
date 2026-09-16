"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { formatMoney, getCached } from "@/lib/api";

type Route = { route_code: string; origin: string; destination: string };
type Flight = {
  id: number;
  airline: string;
  airline_code: string;
  flight_number: string;
  fare_class: string;
  base_fare: number;
  taxes: number;
  fees: number;
  total_fare: number;
  currency: string;
  collected_at: string;
  available: boolean;
};
type Response = { route: string; advance_days: number; recommendation: string; items: Flight[] };

export default function ComparePage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [route, setRoute] = useState("DEL-BOM");
  const [advance, setAdvance] = useState("7");
  const [result, setResult] = useState<Response | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadRoutes = async () => {
      const items = await getCached<Route[]>("/api/routes", 40);
      setRoutes(items);
      if (items[0]) setRoute(items[0].route_code);
    };

    void loadRoutes();
  }, []);

  async function compare(forceRefresh = false) {
    setLoading(true);
    setError("");
    try {
      setResult(
        await getCached<Response>(`/api/recommendations?route=${route}&advance_days=${advance}&limit=10`, 40, forceRefresh),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "No matching fares");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (routes.length) void compare();
  }, [routes.length]);

  return (
    <AppShell
      eyebrow="DECISION SUPPORT"
      title="Compare flights"
      description="Compare observed fares and identify the lowest currently stored total fare."
    >
      <section className="filter-panel">
        <label>
          Route
          <select value={route} onChange={(event) => setRoute(event.target.value)}>
            {routes.map((item) => (
              <option key={item.route_code}>{item.route_code}</option>
            ))}
          </select>
        </label>

        <label>
          Advance window
          <select value={advance} onChange={(event) => setAdvance(event.target.value)}>
            {[1, 7, 15, 30, 45].map((days) => (
              <option key={days} value={days}>T+{days}</option>
            ))}
          </select>
        </label>

        <button className="primary-button" onClick={() => void compare(true)} disabled={loading}>
          {loading ? "Comparing..." : "Compare fares"}
        </button>
      </section>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <>
          <section className="recommendation">
            <div>
              <span className="panel-kicker">BEST OBSERVED PRICE</span>
              <strong>{result.items[0] ? formatMoney(result.items[0].total_fare) : "--"}</strong>
              <p>
                {result.items[0]?.airline} · {result.items[0]?.flight_number} · {result.recommendation}
              </p>
            </div>
            <span className="recommendation-badge">LOWEST TOTAL</span>
          </section>

          <section className="flight-list">
            {result.items.map((item) => (
              <article className="flight-card" key={item.id}>
                <div className="flight-row">
                  <span>{item.airline}</span>
                  <b>{item.flight_number}</b>
                  <small>{item.fare_class}</small>
                </div>
                <div className="flight-meta">
                  <span>{item.airline_code}</span>
                  <span>
                    {new Date(item.collected_at).toLocaleString("en-IN", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </span>
                </div>
                <div className="flight-price">
                  <strong>{formatMoney(item.total_fare)}</strong>
                  <small>
                    Base {formatMoney(item.base_fare)} + fees {formatMoney(item.fees)}
                  </small>
                </div>
              </article>
            ))}
          </section>
        </>
      )}
    </AppShell>
  );
}
