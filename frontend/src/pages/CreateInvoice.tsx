/* C:\coding_projects\dev\schoolflow\frontend\src\pages\CreateInvoice.tsx */
/**
 * Create invoice form (minimal). Use student_id, invoice_no, period, due_date, optional amount_due.
 * Line items are derived from the selected fee plan on the backend (no editable items in this form).
 */

import React from "react";
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

export default function CreateInvoice() {
  const { register, handleSubmit } = useForm<FormValues>();
  const create = useCreateInvoice();
  const nav = useNavigate();
  const toast = useToast();

  const onSubmit = async (values: FormValues) => {
    try {
      const payload: any = {
        invoice_no: values.invoice_no,
        student_id: Number(values.student_id),
        period: values.period,
        due_date: values.due_date,
      };

      if (values.amount_due) {
        payload.amount_due = Number(values.amount_due);
      }

      const data = await create.mutateAsync(payload);
      try {
        toast.push("Invoice created");
      } catch {
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

        <input
          {...register("amount_due")}
          placeholder="Amount (optional - usually derived from fee plan)"
          className="w-full border p-2 rounded"
        />
        <p className="text-sm text-gray-600">
          Line items on the invoice are automatically derived from the selected fee plan.
        </p>

        <div>
          <button type="submit" className="w-full bg-green-600 text-white p-2 rounded">
            Create
          </button>
        </div>
      </form>
    </div>
  );
}
