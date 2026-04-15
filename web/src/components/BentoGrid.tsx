"use client";

import { ReactNode } from "react";
import Card from "./Card";

interface BentoGridProps {
  children: ReactNode;
  className?: string;
}

interface BentoItemProps {
  children: ReactNode;
  className?: string;
  span?: 1 | 2 | 3 | 4;
  variant?: "default" | "accent" | "glow";
  accentColor?: "violet" | "green" | "orange" | "pink" | "cyan";
}

export function BentoGrid({ children, className = "" }: BentoGridProps) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4 ${className}`}>
      {children}
    </div>
  );
}

export function BentoItem({
  children,
  className = "",
  span = 1,
  variant = "default",
  accentColor = "violet",
}: BentoItemProps) {
  const spanClasses = {
    1: "col-span-1",
    2: "md:col-span-2",
    3: "md:col-span-3",
    4: "md:col-span-4",
  };

  return (
    <div className={`${spanClasses[span]} ${className}`}>
      <Card variant={variant} accentColor={accentColor} className="h-full">
        {children}
      </Card>
    </div>
  );
}
