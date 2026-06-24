import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SENTINEL AI — Industrial Safety Intelligence OS",
  description: "Next-generation compound risk detection and emergency response platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-bg text-text font-sans antialiased">{children}</body>
    </html>
  );
}
