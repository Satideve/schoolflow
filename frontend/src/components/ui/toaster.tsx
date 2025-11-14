// C:\coding_projects\dev\schoolflow\frontend\src\components\ui\toaster.tsx
import React from "react";
import ToastItem from "./toast";

export const Toaster: React.FC<{ toasts: Array<{ id: string; message: string }> }> = ({ toasts }) => {
  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
      {toasts.map((t) => (
        <ToastItem key={t.id} message={t.message} />
      ))}
    </div>
  );
};

export default Toaster;
