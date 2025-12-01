/* C:\coding_projects\dev\schoolflow\frontend\src\components\ui\use-toast.tsx */
import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from "react";
import Toaster from "./toaster";

type Toast = { id: string; message: string };

export type ToastContextValue = {
  push: (msg: string) => void;
};

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const ToastProvider: React.FC<{ children?: React.ReactNode }> = ({
  children,
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((message: string) => {
    const id = Math.random().toString(36).slice(2, 9);
    const t: Toast = { id, message };
    console.log("[ToastProvider] push called:", t); // DEBUG
    setToasts((s) => [t, ...s]);
    setTimeout(() => {
      setToasts((s) => s.filter((x) => x.id !== id));
    }, 4000);
  }, []);

  useEffect(() => {
    console.log("[ToastProvider] toasts state changed:", toasts); // DEBUG
  }, [toasts]);

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <Toaster toasts={toasts} />
    </ToastContext.Provider>
  );
};

/**
 * Hook to access the toast context.
 * This is exported as a **named export** used across the app.
 */
export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    console.error("useToast called outside ToastProvider"); // DEBUG
    throw new Error("useToast must be used inside ToastProvider");
  }
  return ctx;
}

export default useToast;
