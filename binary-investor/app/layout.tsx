import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Geist_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SheepOrSleep — AI Behavioral Bias Detector for Indian Stocks",
  description:
    "Detect herding behavior, panic selling, and behavioral gaps in Indian stock markets using the CCK econometric model and Groq AI. Free one-tap comprehensive analysis.",
  keywords: [
    "Indian stocks",
    "behavioral finance",
    "herding detection",
    "panic selling",
    "SIP calculator",
    "NIFTY 50",
    "SENSEX",
    "AI copilot",
    "Monte Carlo",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
