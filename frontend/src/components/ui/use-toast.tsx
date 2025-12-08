// src/components/ui/use-toast.tsx

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import Toaster from "./toaster";

export type ToastEntry = {
  id: string;
  message: string;
};

export type ToastContextValue = {
  push: (message: string) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastEntry[]>([]);

  const push = useCallback((message: string) => {
    const id = Math.random().toString(36).slice(2, 9);

    const entry: ToastEntry = { id, message };
    console.log("[ToastProvider] push called:", entry);

    setToasts((prev) => {
      const next = [...prev, entry];
      console.log("[ToastProvider] toasts state changed:", next);
      return next;
    });

    // Auto-remove after 3 seconds
    setTimeout(() => {
      setToasts((prev) => {
        const next = prev.filter((t) => t.id !== id);
        console.log("[ToastProvider] toasts state changed:", next);
        return next;
      });
    }, 3000);
  }, []);

  useEffect(() => {
    console.log("[ToastProvider] mounted");
  }, []);

  return (
    <ToastContext.Provider value={{ push }}>
      {children}

      {/* Render all toast notifications */}
      <Toaster toasts={toasts} />
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within a ToastProvider");
  return ctx;
}
