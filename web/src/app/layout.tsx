import type { Metadata } from "next";
import { AuthProvider } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";
import AuthGate from "@/components/AuthGate";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "ECHO.OS | Emotional Chronicle",
  description: "High-energy emotive AI mental health companion.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen bg-bg-primary text-white selection:bg-neon-green selection:text-black overflow-x-hidden scanlines">
        {/* Global OS FX */}
        <div className="noise-overlay" />

        <AuthProvider>
          <AuthGate title="ECHO.OS">
            <Navbar />
            <div className="md:pl-[72px] min-h-screen relative z-10 transition-all duration-300">
              {children}
            </div>
          </AuthGate>
        </AuthProvider>
      </body>
    </html>
  );
}
