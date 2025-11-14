// C:\coding_projects\dev\schoolflow\frontend\src\components\ui\input.tsx
import React from "react";

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
};

export const Input: React.FC<InputProps> = ({ label, className = "", ...props }) => {
  return (
    <div className="flex flex-col gap-1">
      {label && <label className="text-sm text-slate-700 dark:text-slate-200">{label}</label>}
      <input
        {...props}
        className={`rounded-md border border-slate-200 dark:border-slate-700 px-3 py-2 bg-white dark:bg-gray-900 text-sm ${className}`}
      />
    </div>
  );
};

export default Input;
