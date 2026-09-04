"use client";
import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { formatMoney, get } from "@/lib/api";
type Item = { route: string; standard_deviation: number; coefficient_of_variation: number };
export default function VolatilityPage() { const [items, setItems] = useState<Item[]>([]); useEffect(() => { get<Item[]>("/api/analytics/volatility").then(setItems); }, []); return <AppShell eyebrow="ROUTE PRESSURE" title="Volatility" description="Routes ranked by dispersion and coefficient of variation."><section className="panel page-panel"><div className="table-wrap"><table><thead><tr><th>Rank</th><th>Route</th><th>Std. deviation</th><th>Coefficient of variation</th><th>Signal</th></tr></thead><tbody>{items.map((item, index) => <tr key={item.route}><td>0{index + 1}</td><td><b>{item.route}</b></td><td>{formatMoney(item.standard_deviation)}</td><td>{item.coefficient_of_variation.toFixed(2)}%</td><td><span className="signal">{item.coefficient_of_variation > 25 ? "High movement" : "Stable"}</span></td></tr>)}</tbody></table></div></section></AppShell>; }
