"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { formatPercent, get } from "@/lib/api";

type Cpi = { date: string; cpi_value: number; daily_change: number; weekly_change: number; monthly_change: number; sample_count: number; base_period: string };
type Daily = { date: string; index_value: number; sample_count: number };

function Chart({ values }: { values: Daily[] }) {
  const max = Math.max(...values.map((item) => item.index_value), 1), min = Math.min(...values.map((item) => item.index_value), 100), range = max - min || 1;
  const points = values.map((item, index) => `${(index / Math.max(values.length - 1, 1)) * 800},${210 - ((item.index_value - min) / range) * 170}`).join(" ");
  return <div className="wide-chart"><svg viewBox="0 0 800 230"><polyline points={points} fill="none" stroke="#168d83" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />{values.map((item, index) => <circle key={item.date} cx={(index / Math.max(values.length - 1, 1)) * 800} cy={210 - ((item.index_value - min) / range) * 170} r="3" fill="#f5b84b" />)}</svg></div>;
}

export default function CpiPage() {
  const [cpi, setCpi] = useState<Cpi | null>(null), [daily, setDaily] = useState<Daily[]>([]), [error, setError] = useState<string | null>(null);
  useEffect(() => { Promise.all([get<Cpi>("/api/cpi/current"), get<Daily[]>("/api/index/daily")]).then(([current, history]) => { setCpi(current); setDaily(history); }).catch((err) => setError(err.message)); }, []);
  return <AppShell eyebrow="INDEX METHODOLOGY" title="Consumer Price Index" description="The dedicated composite airfare index calculated from stored route medians and configurable weights.">{error && <div className="error-banner">{error}</div>}<section className="cpi-hero"><div><span className="panel-kicker">CURRENT APIx / CPI PROXY</span><strong>{cpi?.cpi_value.toFixed(2) || "--"}</strong><p>Base period: {cpi?.base_period || "--"}</p></div><div className="cpi-change"><span>Daily</span><b>{formatPercent(cpi?.daily_change)}</b><span>Weekly</span><b>{formatPercent(cpi?.weekly_change)}</b><span>Monthly</span><b>{formatPercent(cpi?.monthly_change)}</b></div></section><section className="panel page-panel"><div className="panel-head"><div><div className="panel-kicker">30-DAY HISTORY</div><h2>Composite airfare movement</h2></div><span className="muted">{cpi?.sample_count || 0} latest samples</span></div><Chart values={daily} /></section><section className="method-grid"><article className="panel page-panel"><div className="panel-kicker">FORMULA</div><h2>How CPI is calculated</h2><p className="body-copy">Each route median is compared with its first-seven-day base fare, converted to a price relative, then combined using normalized prototype route weights.</p><code>Σ(route weight × route relative)</code></article><article className="panel page-panel"><div className="panel-kicker">INTERPRETATION</div><h2>Read the signal</h2><p className="body-copy">A value above 100 indicates fares are higher than the configured base period. This is a prototype methodology and does not claim to reproduce official CPI.</p></article></section></AppShell>;
}
