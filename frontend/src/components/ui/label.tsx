// C:\coding_projects\dev\schoolflow\frontend\src\components\ui\label.tsx
import React from "react";

export const Label: React.FC<{ children?: React.ReactNode; className?: string }> = ({ children, className = "" }) => {
  return <label className={`text-sm font-medium text-slate-700 dark:text-slate-200 ${className}`}>{children}</label>;
};

export default Label;
