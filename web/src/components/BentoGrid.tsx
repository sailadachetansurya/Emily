"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";
import Card from "./Card";

interface BentoGridProps {
  children: ReactNode;
  className?: string;
}

interface BentoItemProps {
  children: ReactNode;
  className?: string;
  span?: 1 | 2 | 3 | 4;
  accent?: "violet" | "green" | "orange" | "pink" | "cyan" | "none";
  label?: string;
}

export function BentoGrid({ children, className = "" }: BentoGridProps) {
  return (
    <motion.div
      initial="hidden"
      animate="show"
      variants={{
        hidden: { opacity: 0 },
        show: {
          opacity: 1,
          transition: { staggerChildren: 0.1 },
        },
      }}
      className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-5 ${className}`}
    >
      {children}
    </motion.div>
  );
}

export function BentoItem({
  children,
  className = "",
  span = 1,
  accent = "none",
  label,
}: BentoItemProps) {
  const spanClasses = {
    1: "col-span-1",
    2: "col-span-1 md:col-span-2",
    3: "col-span-1 md:col-span-2 lg:col-span-3",
    4: "col-span-1 md:col-span-2 lg:col-span-3 xl:col-span-4",
  };

  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } },
      }}
      className={`${spanClasses[span]} ${className}`}
    >
      <Card accent={accent} label={label} className="h-full flex flex-col">
        {children}
      </Card>
    </motion.div>
  );
}
