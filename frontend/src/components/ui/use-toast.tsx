/* C:\coding_projects\dev\schoolflow\frontend\src\components\ui\use-toast.tsx */
import React, { createContext, useContext, useState, useCallback } from "react";
import Toaster from "./toaster";

type Toast = { id: string; message: string };

const ToastContext = createContext<{ push: (msg: string) => void } | undefined>(undefined);

export const ToastProvider: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((message: string) => {
    const id = Math.random().toString(36).slice(2, 9);
    const t: Toast = { id, message };
    setToasts((s) => [t, ...s]);
    setTimeout(() => setToasts((s) => s.filter((x) => x.id !== id)), 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <Toaster toasts={toasts} />
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
};

export default useToast;
