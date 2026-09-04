import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VAYU | Airfare Price Index",
  description: "India domestic airfare intelligence dashboard",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en"><body>{children}</body></html>
  );
}
