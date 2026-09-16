"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { getCached } from "@/lib/api";

type RouteRow = { route_code: string; origin: string; destination: string; weight: number; active: boolean };
export default function RoutesPage() { const [routes, setRoutes] = useState<RouteRow[]>([]); const [error, setError] = useState(""); const load = async (forceRefresh = false) => { try { const data = await getCached<RouteRow[]>("/api/routes", 40, forceRefresh); setRoutes(data); } catch (e) { setError(e instanceof Error ? e.message : "Unable to load routes"); } }; useEffect(() => { void load(); }, []); return <AppShell eyebrow="NETWORK COVERAGE" title="Routes" description="The configurable domestic route basket feeding APIx.">{error && <div className="error-banner">{error}</div>}<button className="primary-button" style={{ marginBottom: 18 }} onClick={() => void load(true)}>Sync data</button><section className="route-cards">{routes.map((route) => <Link href={`/compare?route=${route.route_code}`} className="route-card" key={route.route_code}><span>{route.origin}</span><b>→</b><span>{route.destination}</span><small>Weight {route.weight.toFixed(2)} · Compare fares</small></Link>)}</section></AppShell>; }
