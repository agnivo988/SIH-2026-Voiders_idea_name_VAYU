"use client";

import Link from "next/link";
import { Activity, BarChart3, ChevronLeft, Database, Gauge, Plane, Search, Route, ShieldCheck } from "lucide-react";
import { useState } from "react";

const navigation = [
  ["Overview", "/", Gauge], ["CPI index", "/cpi", BarChart3], ["Routes", "/routes", Route],
  ["Compare flights", "/compare", Search], ["Lead time", "/lead-time", BarChart3],
  ["Airlines", "/airlines", Plane], ["Volatility", "/volatility", Activity], ["Data quality", "/data-quality", Database],
] as const;

export default function Sidebar({ active }: { active?: string }) {
  const [collapsed, setCollapsed] = useState(false);
  return <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
    <div className="brand-row"><Link href="/" className="brand"><span className="brand-mark"><Plane size={20} /></span><span className="brand-copy"><strong>VAYU</strong><small>Airfare intelligence</small></span></Link><button className="collapse-button" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} title={collapsed ? "Expand sidebar" : "Collapse sidebar"}><ChevronLeft size={17} /></button></div>
    <div className="nav-label">Workspace</div>
    <nav>{navigation.map(([label, href, Icon]) => <Link key={href} href={href} className={`nav-item ${active === href ? "active" : ""}`} title={collapsed ? label : undefined}><Icon size={17} /><span>{label}</span></Link>)}</nav>
    <div className="sidebar-foot"><ShieldCheck size={16} /><span>Ethical collection<br /><b>Source controls active</b></span></div>
  </aside>;
}
