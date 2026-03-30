import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TradeOS — Institutional Stock Intelligence Platform",
  description:
    "Professional-grade stock analysis with 40+ technical indicators, AI-powered trading decisions, and real-time global market intelligence. BUY/SELL/HOLD signals with entry, stop-loss, and target prices.",
  keywords: [
    "stock analysis", "trading signals", "technical indicators",
    "AI trading", "market intelligence", "buy sell hold",
    "NIFTY 50", "NYSE", "global stocks",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            try {
              var theme = localStorage.getItem('tradeos-theme');
              if (theme === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
              else if (theme === 'light') document.documentElement.removeAttribute('data-theme');
              else if (window.matchMedia('(prefers-color-scheme: dark)').matches) document.documentElement.setAttribute('data-theme', 'dark');
            } catch(e) {}
          })();
        `}} />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}