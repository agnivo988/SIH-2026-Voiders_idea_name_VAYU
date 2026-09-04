"use client";
import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { formatMoney, get } from "@/lib/api";
type Airline = { airline: string; median_fare: number; average_fare: number; observations: number };
export default function AirlinesPage() { const [items, setItems] = useState<Airline[]>([]); useEffect(() => { get<Airline[]>("/api/analytics/airlines").then(setItems); }, []); return <AppShell eyebrow="CARRIER COMPARISON" title="Airlines" description="Observed fare levels across the carrier set in the database."><section className="panel page-panel"><div className="table-wrap"><table><thead><tr><th>Airline</th><th>Median fare</th><th>Average fare</th><th>Observations</th></tr></thead><tbody>{items.map((item) => <tr key={item.airline}><td><b>{item.airline}</b></td><td>{formatMoney(item.median_fare)}</td><td>{formatMoney(item.average_fare)}</td><td>{item.observations.toLocaleString("en-IN")}</td></tr>)}</tbody></table></div></section></AppShell>; }
