/* C:\coding_projects\dev\schoolflow\frontend\src\components\ui\button.tsx */
import React from "react";
import { cn } from "../../lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
};

const VARIANT_CLASSES: Record<string, string> = {
  default: "bg-slate-900 text-white hover:bg-slate-800",
  ghost: "bg-transparent text-slate-900 hover:bg-slate-100",
  danger: "bg-red-600 text-white hover:bg-red-700",
};

const SIZE_CLASSES: Record<string, string> = {
  sm: "px-2 py-1 text-sm",
  md: "px-3 py-2 text-sm",
  lg: "px-4 py-2 text-base",
};

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, className, variant = "default", size = "md", disabled, ...rest }, ref) => {
    const classes = cn(
      "inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed",
      VARIANT_CLASSES[variant],
      SIZE_CLASSES[size],
      className ?? ""
    );

    return (
      <button
        ref={ref}
        disabled={disabled}
        aria-disabled={disabled}
        className={classes}
        {...rest}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
