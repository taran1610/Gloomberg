import type { Metadata } from "next";
import "./globals.css";
import TerminalHeader from "@/components/TerminalHeader";
import TickerTape from "@/components/TickerTape";
import WaitlistPopup from "@/components/WaitlistPopup";
import { AuthProvider } from "@/lib/auth";

export const metadata: Metadata = {
  title: "GLOOMBERG TERMINAL",
  description: "AI-powered financial research terminal",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-term-black text-term-text font-terminal" suppressHydrationWarning>
        <AuthProvider>
          <div className="terminal-glow terminal-side-glow flex flex-col h-screen overflow-hidden">
            <TerminalHeader />
            <main className="flex-1 overflow-auto relative z-10">{children}</main>
            <TickerTape />
          </div>
          <WaitlistPopup />
        </AuthProvider>
      </body>
    </html>
  );
}
