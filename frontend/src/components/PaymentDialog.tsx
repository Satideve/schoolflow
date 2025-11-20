/* C:\coding_projects\dev\schoolflow\frontend\src\components\PaymentDialog.tsx */
/**
 * PaymentDialog — modal used to collect payment details. Renders into document.body via portal.
 * Improved centering and visibility: uses fixed top/left + transform centering, higher z-index,
 * and max-height with internal scrolling to ensure it is always visible and usable.
 */

import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: { amount: number; provider: string; note?: string }) => void;
  loading?: boolean;
};

export default function PaymentDialog({ open, onOpenChange, onSubmit, loading }: Props) {
  const [amount, setAmount] = useState<string>("");
  const [provider, setProvider] = useState<string>("manual");
  const [note, setNote] = useState<string>("");

  useEffect(() => {
    if (!open) {
      setAmount("");
      setProvider("manual");
      setNote("");
    } else {
      console.log("PaymentDialog opened — portal should be mounted to document.body");
      // small debug: log viewport height and scroll position
      console.log("viewport height:", window.innerHeight, "scrollY:", window.scrollY);
    }
  }, [open]);

  function handleClose() {
    onOpenChange(false);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const numeric = Number(amount);
    if (Number.isNaN(numeric) || numeric <= 0) {
      alert("Please enter a valid amount greater than 0");
      return;
    }
    onSubmit({ amount: numeric, provider, note: note?.trim() || undefined });
  }

  if (!open) return null;

  const modalWrapperStyle: React.CSSProperties = {
    position: "fixed",
    inset: 0,
    zIndex: 99999,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  };

  const dialogStyle: React.CSSProperties = {
    position: "fixed",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    width: "min(720px, 95%)",
    maxHeight: "90vh",
    overflow: "auto",
  };

  const modal = (
    <div style={modalWrapperStyle} data-payment-dialog>
      <div
        className="absolute inset-0 bg-black/50"
        onClick={handleClose}
        aria-hidden="true"
        style={{ zIndex: 99998 }}
      />
      <div role="dialog" aria-modal="true" style={dialogStyle} className="relative z-[99999] bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold">Collect Payment</h3>
          <button onClick={handleClose} aria-label="Close" className="text-sm text-gray-700 hover:underline">
            Close
          </button>
        </div>

        <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-sm font-medium text-gray-700">Amount</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="mt-1 block w-full rounded border px-3 py-2"
              placeholder="Enter amount"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="mt-1 block w-full rounded border px-3 py-2"
            >
              <option value="manual">Manual</option>
              <option value="fake">Fake (test)</option>
              <option value="razorpay">Razorpay</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Note (optional)</label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="mt-1 block w-full rounded border px-3 py-2"
              rows={3}
              placeholder="Enter a note or receipt memo"
            />
          </div>

          <div className="flex items-center justify-end space-x-2">
            <button
              type="button"
              onClick={handleClose}
              className="px-3 py-1 rounded border"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-60"
              disabled={loading}
            >
              {loading ? "Processing..." : "Submit Payment"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
