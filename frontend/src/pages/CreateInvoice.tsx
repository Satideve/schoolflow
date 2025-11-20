/* C:\coding_projects\dev\schoolflow\frontend\src\pages\CreateInvoice.tsx */
/**
 * Create invoice form (minimal). Use student_id, invoice_no, period, due_date, optional amount_due.
 * Added dynamic Line Items entry so frontend can create invoices with fee components.
 */

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { useCreateInvoice } from "../api/queries";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ui/use-toast";

type FormValues = {
  invoice_no: string;
  student_id: string;
  period: string;
  due_date: string;
  amount_due?: string;
};

type LineItem = {
  description: string;
  amount: string; // keep as string for easy input handling
};

export default function CreateInvoice() {
  const { register, handleSubmit } = useForm<FormValues>();
  const create = useCreateInvoice();
  const nav = useNavigate();
  const toast = useToast();

  const [items, setItems] = useState<LineItem[]>([
    { description: "", amount: "" }
  ]);

  function addItem() {
    setItems((s) => [...s, { description: "", amount: "" }]);
  }

  function removeItem(index: number) {
    setItems((s) => s.filter((_, i) => i !== index));
  }

  function updateItem(index: number, field: keyof LineItem, value: string) {
    setItems((s) => s.map((it, i) => (i === index ? { ...it, [field]: value } : it)));
  }

  const onSubmit = async (values: FormValues) => {
    try {
      // build items payload (only include items with a description or amount)
      const preparedItems = items
        .map((it) => ({
          description: it.description?.trim(),
          amount: it.amount ? Number(it.amount) : 0,
        }))
        .filter((it) => (it.description && !Number.isNaN(it.amount)) || it.amount > 0);

      // compute amount_due from items if user didn't provide one
      const computedAmountDue =
        preparedItems.length > 0
          ? preparedItems.reduce((s, it) => s + (Number(it.amount) || 0), 0)
          : undefined;

      const payload: any = {
        invoice_no: values.invoice_no,
        student_id: Number(values.student_id),
        period: values.period,
        due_date: values.due_date,
      };

      if (values.amount_due) {
        payload.amount_due = Number(values.amount_due);
      } else if (typeof computedAmountDue !== "undefined") {
        payload.amount_due = computedAmountDue;
      }

      if (preparedItems.length > 0) {
        payload.items = preparedItems.map((it) => ({
          description: it.description,
          amount: it.amount,
        }));
      }

      const data = await create.mutateAsync(payload);
      // keep existing toast usage (push)
      try {
        toast.push("Invoice created");
      } catch {
        // fallback if toast API differs
        console.log("Invoice created");
      }
      nav(`/invoices/${data.id}`);
    } catch (err: any) {
      console.error("create invoice error", err);
      try {
        toast.push("Create failed");
      } catch {
        console.log("Create failed");
      }
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white p-6 rounded shadow">
      <h2 className="text-xl mb-4">Create Invoice</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <input
          {...register("invoice_no", { required: true })}
          placeholder="Invoice No"
          className="w-full border p-2 rounded"
        />
        <input
          {...register("student_id", { required: true })}
          placeholder="Student ID"
          className="w-full border p-2 rounded"
        />
        <input
          {...register("period", { required: true })}
          placeholder="Period (e.g., 2025-02)"
          className="w-full border p-2 rounded"
        />
        <input
          {...register("due_date", { required: true })}
          placeholder="Due Date (YYYY-MM-DD)"
          className="w-full border p-2 rounded"
        />

        <div className="border rounded p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium">Line Items</div>
            <button
              type="button"
              onClick={addItem}
              className="text-sm px-2 py-1 rounded bg-blue-600 text-white"
            >
              + Add item
            </button>
          </div>

          <div className="space-y-2">
            {items.map((it, idx) => (
              <div key={idx} className="flex gap-2 items-center">
                <input
                  value={it.description}
                  onChange={(e) => updateItem(idx, "description", e.target.value)}
                  placeholder="Description"
                  className="flex-1 border p-2 rounded"
                />
                <input
                  value={it.amount}
                  onChange={(e) => updateItem(idx, "amount", e.target.value)}
                  placeholder="Amount"
                  className="w-32 border p-2 rounded text-right"
                />
                <button
                  type="button"
                  onClick={() => removeItem(idx)}
                  className="px-2 py-1 rounded bg-red-500 text-white text-sm"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>

        <input
          {...register("amount_due")}
          placeholder="Amount (optional - will be computed from items if left blank)"
          className="w-full border p-2 rounded"
        />

        <div>
          <button type="submit" className="w-full bg-green-600 text-white p-2 rounded">
            Create
          </button>
        </div>
      </form>
    </div>
  );
}
