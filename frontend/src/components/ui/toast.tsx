// C:\coding_projects\dev\schoolflow\frontend\src\components\ui\toast.tsx
import React from "react";

export const ToastItem: React.FC<{ message: string; id?: string }> = ({
  message,
}) => {
  return (
    <div className="max-w-sm w-full bg-slate-900 text-white shadow-lg rounded-md px-4 py-3 border border-slate-700">
      <div className="text-sm font-medium">{message}</div>
    </div>
  );
};

export default ToastItem;
