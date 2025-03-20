import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CampaignOps · Campaign intelligence & content operations",
  description: "Trace campaign performance from source exports to WordPress content and verified test journeys. An independent portfolio demonstration.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
