"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { get } from "@/lib/api";

type RouteRow = { route_code: string; origin: string; destination: string; weight: number; active: boolean };
export default function RoutesPage() { const [routes, setRoutes] = useState<RouteRow[]>([]); const [error, setError] = useState(""); useEffect(() => { get<RouteRow[]>("/api/routes").then(setRoutes).catch((e) => setError(e.message)); }, []); return <AppShell eyebrow="NETWORK COVERAGE" title="Routes" description="The configurable domestic route basket feeding APIx.">{error && <div className="error-banner">{error}</div>}<section className="route-cards">{routes.map((route) => <Link href={`/compare?route=${route.route_code}`} className="route-card" key={route.route_code}><span>{route.origin}</span><b>→</b><span>{route.destination}</span><small>Weight {route.weight.toFixed(2)} · Compare fares</small></Link>)}</section></AppShell>; }
