/* C:\coding_projects\dev\schoolflow\frontend\src\components\ui\badge.tsx */
import * as React from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "warning" | "destructive" | "outline";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantClasses = {
    default: "bg-slate-200 text-slate-800",
    success: "bg-green-200 text-green-800",
    warning: "bg-yellow-200 text-yellow-800",
    destructive: "bg-red-200 text-red-800",
    outline: "border border-slate-300 text-slate-700",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
}
