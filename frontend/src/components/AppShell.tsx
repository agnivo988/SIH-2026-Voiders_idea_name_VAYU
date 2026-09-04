"use client";

import { Plane } from "lucide-react";
import Sidebar from "@/components/Sidebar";

export default function AppShell({ children, eyebrow, title, description }: { children: React.ReactNode; eyebrow: string; title: string; description: string }) {
  const active = title === "Airfare Price Index" ? "/" : title === "Consumer Price Index" ? "/cpi" : title.toLowerCase().replaceAll(" ", "-");
  return <main className="shell"><Sidebar active={active} /><section className="content"><header className="topbar"><div className="mobile-brand"><Plane size={18} /> VAYU</div><div className="status"><span className="pulse" /> Supabase connected <span className="divider" /> Stored observations</div></header><div className="page-head"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div><div className="data-badge"><span /> DEMO SOURCE DATA</div></div>{children}</section></main>;
}
