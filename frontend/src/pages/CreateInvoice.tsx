/* C:\coding_projects\dev\schoolflow\frontend\src\pages\CreateInvoice.tsx */
/**
 * Create invoice form (admin).
 *
 * - Core fields: invoice_no, student_id, period, due_date.
 * - Base amount_due field (optional).
 * - Line items section where admin can enter extra charges.
 *
 * Backend still receives:
 *   - amount_due (base/top-up)
 *   - line_items[] (per-item charges) for the invoice.
 */

import React, { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import {
  useCreateInvoice,
  useStudents,
  useFeeAssignments,
} from "../api/queries";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ui/use-toast";
import type { InvoiceCreateDTO } from "../types/api";

type FormValues = {
  invoice_no: string;
  student_id: string;
  period: string;
  due_date: string;
  amount_due?: string; // base amount (optional)
};

type LineItem = {
  description: string;
  amount: string;
};

export default function CreateInvoice() {
  const {
    register,
    handleSubmit,
    watch,
    formState: { isSubmitting },
  } = useForm<FormValues>();

  const [items, setItems] = useState<LineItem[]>([]);
  const create = useCreateInvoice();
  const nav = useNavigate();
  const toast = useToast();

  const { data: studentsData } = useStudents();
  const { data: assignmentsData } = useFeeAssignments();

  // Watch the base amount field
  const baseAmountField = watch("amount_due") || "";

  // Totals
  const itemsTotal = useMemo(() => {
    return items.reduce((sum, it) => {
      const n = Number(it.amount);
      if (!Number.isNaN(n) && n > 0) {
        return sum + n;
      }
      return sum;
    }, 0);
  }, [items]);

  const baseAmount = useMemo(() => {
    const n = Number(baseAmountField);
    return !Number.isNaN(n) && n > 0 ? n : 0;
  }, [baseAmountField]);

  const grandTotal = useMemo(() => {
    return baseAmount + itemsTotal;
  }, [baseAmount, itemsTotal]);

  // Build student → object map
  const studentMap = useMemo(() => {
    const map = new Map<number, any>();
    (studentsData ?? []).forEach((s: any) => {
      if (s?.id != null) map.set(Number(s.id), s);
    });
    return map;
  }, [studentsData]);

  // Build student → fee_assignment map
  const assignmentMap = useMemo(() => {
    const map = new Map<number, any>();
    (assignmentsData ?? []).forEach((a: any) => {
      if (a?.student_id != null) map.set(Number(a.student_id), a);
    });
    return map;
  }, [assignmentsData]);

  const handleAddItem = () => {
    setItems((prev) => [...prev, { description: "", amount: "" }]);
  };

  const handleRemoveItem = (index: number) => {
    setItems((prev) => prev.filter((_, i) => i !== index));
  };

  const handleItemChange = (
    index: number,
    field: keyof LineItem,
    value: string,
  ) => {
    setItems((prev) =>
      prev.map((it, i) =>
        i === index
          ? {
              ...it,
              [field]: value,
            }
          : it,
      ),
    );
  };

  const onSubmit = async (values: FormValues) => {
    try {
      const studentId = Number(values.student_id);

      // 1) Validate student ID is numeric
      if (!studentId || Number.isNaN(studentId)) {
        toast.push("Please enter a valid numeric student ID.");
        return;
      }

      // 2) Check that the student exists
      if (!studentMap.has(studentId)) {
        toast.push(`Student ID ${studentId} does not exist.`);
        return;
      }

      // 3) Check that the student has a fee assignment
      if (!assignmentMap.has(studentId)) {
        const student = studentMap.get(studentId);
        const label = student?.name ?? `Student #${studentId}`;
        toast.push(
          `${label} has no fee plan assignment. Please assign a fee plan first.`,
        );
        // Redirect to Fee Assignments page
        nav("/fee-assignments");
        return;
      }

      // base payload (without totals logic)
      const payload: InvoiceCreateDTO = {
        invoice_no: values.invoice_no,
        student_id: studentId,
        period: values.period,
        due_date: values.due_date,
      };

      // Base amount (extra / top-up)
      const base = baseAmount; // already sanitized via useMemo
      if (base > 0) {
        payload.amount_due = base;
      } else {
        payload.amount_due = null;
      }

      // Map local line items -> backend shape
      const line_items = items
        .map((it) => {
          const n = Number(it.amount);
          const desc = it.description?.trim() ?? "";
          if (!desc || Number.isNaN(n) || n <= 0) {
            return null;
          }
          return {
            description: desc,
            amount: n,
          };
        })
        .filter(
          (it): it is { description: string; amount: number } => it !== null,
        );

      if (line_items.length > 0) {
        // Cast to any to satisfy TS if InvoiceCreateDTO doesn't declare line_items
        (payload as any).line_items = line_items;
      }

      const data = await create.mutateAsync(payload);

      toast.push("Invoice created");

      nav(`/invoices/${data.id}`);
    } catch (err: any) {
      console.error("create invoice error", err);

      const message =
        err?.response?.data?.detail ??
        "Unable to create invoice. Please check the form and try again.";

      toast.push(`Create failed: ${message}`);
    }
  };

  return (
    <div className="max-w-3xl mx-auto bg-white p-6 rounded shadow space-y-6">
      <h2 className="text-2xl font-semibold mb-2">Create Invoice</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Core fields */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium mb-1">
              Invoice No
            </label>
            <input
              {...register("invoice_no", { required: true })}
              placeholder="INV-2025-001"
              className="w-full border p-2 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Student ID
            </label>
            <input
              {...register("student_id", { required: true })}
              placeholder="e.g. 1"
              className="w-full border p-2 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Period
            </label>
            <input
              {...register("period", { required: true })}
              placeholder="e.g., 2025-12"
              className="w-full border p-2 rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Due Date
            </label>
            <input
              {...register("due_date", { required: true })}
              placeholder="YYYY-MM-DD"
              className="w-full border p-2 rounded"
            />
          </div>
        </div>

        {/* Base amount field */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Base Amount (optional)
          </label>
          <input
            {...register("amount_due")}
            placeholder="Base amount, e.g. 3500.00"
            className="w-full border p-2 rounded"
          />
          <p className="mt-1 text-xs text-gray-600">
            This is a base amount. Any line items you add below will be added on
            top of this amount to compute the final invoice total.
          </p>
        </div>

        {/* Line items section */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Line Items (optional)</h3>
            <button
              type="button"
              onClick={handleAddItem}
              className="px-3 py-1 text-sm rounded border border-gray-300 hover:bg-gray-50"
            >
              + Add Item
            </button>
          </div>

          {items.length === 0 ? (
            <p className="text-sm text-gray-600">
              No extra line items. You can still create an invoice using only
              the base amount.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="p-2 text-left">Description</th>
                    <th className="p-2 text-right">Amount</th>
                    <th className="p-2 text-right"></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((it, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="p-2">
                        <input
                          value={it.description}
                          onChange={(e) =>
                            handleItemChange(
                              idx,
                              "description",
                              e.target.value,
                            )
                          }
                          placeholder="e.g. Late fee, Misc charges"
                          className="w-full border px-2 py-1 rounded"
                        />
                      </td>
                      <td className="p-2 text-right">
                        <input
                          value={it.amount}
                          onChange={(e) =>
                            handleItemChange(idx, "amount", e.target.value)
                          }
                          placeholder="e.g. 250.00"
                          className="w-full border px-2 py-1 rounded text-right"
                        />
                      </td>
                      <td className="p-2 text-right">
                        <button
                          type="button"
                          onClick={() => handleRemoveItem(idx)}
                          className="text-xs text-red-600 hover:underline"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Summary */}
          <div className="mt-2 text-sm text-gray-700 space-y-1">
            <div>
              Base amount:{" "}
              <span className="font-semibold">₹{baseAmount.toFixed(2)}</span>
            </div>
            <div>
              Line items total:{" "}
              <span className="font-semibold">₹{itemsTotal.toFixed(2)}</span>
            </div>
            <div>
              <span className="font-semibold">Final invoice amount:</span>{" "}
              <span className="font-bold">₹{grandTotal.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div>
          <button
            type="submit"
            className="w-full bg-green-600 text-white p-2 rounded disabled:opacity-60"
            disabled={isSubmitting || create.isPending}
          >
            {isSubmitting || create.isPending ? "Creating..." : "Create"}
          </button>
        </div>
      </form>
    </div>
  );
}
