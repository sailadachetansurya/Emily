import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "ECHO - Emotional Chronicle",
  description: "Your emotional journey, tracked and understood. A Gen Z mental health companion powered by AI.",
  keywords: ["mental health", "emotional tracking", "AI companion", "Gen Z", "wellness"],
};

import ParticleBackground from "@/components/ParticleBackground";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="antialiased min-h-screen bg-background text-text">
        {/* Animated 3D background */}
        <div className="fixed inset-0 -z-10">
          <ParticleBackground />
        </div>
        {children}
      </body>
    </html>
  );
}
