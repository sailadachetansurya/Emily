import type { Metadata } from "next";
import { AuthProvider } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";
import AuthGate from "@/components/AuthGate";
import ParticleBackground from "@/components/ParticleBackground";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "ECHO | Emotional Chronicle",
  description: "Advanced emotive AI mental health companion.",
  keywords: ["mental health", "AI", "emotive tracking", "wellness", "Gen Z"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen bg-bg-primary text-text-primary selection:bg-neon-violet selection:text-black overflow-x-hidden">
        {/* Global effects */}
        <div className="noise-overlay" />
        <div className="scanlines" />

        <div className="fixed inset-0 -z-10 bg-mesh-gradient">
          <ParticleBackground />
        </div>

        <AuthProvider>
          <AuthGate>
            <Navbar />
            <div className="md:pl-[72px] min-h-screen pb-20 md:pb-0 relative z-10 transition-all duration-300">
              {children}
            </div>
          </AuthGate>
        </AuthProvider>
      </body>
    </html>
  );
}
