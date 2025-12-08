/* C:\coding_projects\dev\schoolflow\frontend\src\pages\FeePlans.tsx */
import React from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import {
  useFeePlans,
  useCreateFeePlan,
  useUpdateFeePlan,
  useDeleteFeePlan,
} from "../api/queries";
import { useToast } from "../components/ui/use-toast";

type FormValues = {
  name: string;
  academic_year: string;
  frequency: string;
};

export default function FeePlans() {
  const { data, isLoading, isError } = useFeePlans();
  const createMutation = useCreateFeePlan();
  const updateMutation = useUpdateFeePlan();
  const deleteMutation = useDeleteFeePlan();

  const { register, handleSubmit, reset } = useForm<FormValues>({
    defaultValues: {
      frequency: "monthly",
    },
  });
  const toast = useToast();

  const plans = Array.isArray(data) ? data : data ?? [];

  // Inline edit state
  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [editingName, setEditingName] = React.useState<string>("");
  const [editingYear, setEditingYear] = React.useState<string>("");
  const [editingFrequency, setEditingFrequency] = React.useState<string>("");

  const onSubmit = async (values: FormValues) => {
    try {
      await createMutation.mutateAsync({
        name: values.name.trim(),
        academic_year: values.academic_year.trim(),
        frequency: values.frequency,
      });
      reset({ name: "", academic_year: "", frequency: "monthly" });
      try {
        toast.push(`Fee plan created: ${values.name}`);
      } catch {
        console.log("Fee plan created");
      }
    } catch (err) {
      console.error("create fee plan failed", err);
      try {
        toast.push("Create fee plan failed");
      } catch {
        console.log("Create fee plan failed");
      }
    }
  };

  const startEditing = (p: any) => {
    setEditingId(p.id);
    setEditingName(p.name ?? "");
    setEditingYear(p.academic_year ?? "");
    setEditingFrequency(p.frequency ?? "monthly");
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditingName("");
    setEditingYear("");
    setEditingFrequency("monthly");
  };

  const saveEdit = async (id: number) => {
    const name = editingName.trim();
    const academic_year = editingYear.trim();
    const frequency = editingFrequency || "monthly";

    if (!name || !academic_year) {
      try {
        toast.push("Name and academic year are required.");
      } catch {
        console.log("Name and academic year are required.");
      }
      return;
    }

    try {
      await updateMutation.mutateAsync({
        id,
        name,
        academic_year,
        frequency,
      });
      cancelEditing();
      try {
        toast.push("Fee plan updated.");
      } catch {
        console.log("Fee plan updated.");
      }
    } catch (err) {
      console.error("update fee plan failed", err);
      try {
        toast.push("Failed to update fee plan.");
      } catch {
        console.log("Failed to update fee plan.");
      }
    }
  };

  const handleDelete = async (id: number) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this fee plan? This will not delete existing invoices."
    );
    if (!confirmed) return;

    try {
      await deleteMutation.mutateAsync(id);
      try {
        toast.push("Fee plan deleted.");
      } catch {
        console.log("Fee plan deleted.");
      }
    } catch (err) {
      console.error("delete fee plan failed", err);
      try {
        toast.push("Failed to delete fee plan.");
      } catch {
        console.log("Failed to delete fee plan.");
      }
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Fee Plans</h1>

      {/* Create form */}
      <div className="bg-white rounded shadow p-4">
        <h2 className="text-lg font-semibold mb-3">Add Fee Plan</h2>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex flex-col gap-3 max-w-md"
        >
          <input
            {...register("name", { required: true })}
            placeholder="Plan name (e.g., Standard-IX-2025)"
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            {...register("academic_year", { required: true })}
            placeholder="Academic year (e.g., 2025-2026 or 2025)"
            className="border rounded px-3 py-2 text-sm"
          />
          <select
            {...register("frequency", { required: true })}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="monthly">Monthly</option>
            <option value="termly">Termly</option>
            <option value="yearly">Yearly</option>
          </select>
          <button
            type="submit"
            disabled={(createMutation as any).isPending}
            className="inline-flex items-center justify-center px-4 py-2 rounded bg-blue-600 text-white text-sm disabled:opacity-60"
          >
            {(createMutation as any).isPending ? "Saving..." : "Create"}
          </button>
        </form>
      </div>

      {/* List + edit/delete */}
      <div className="bg-white rounded shadow p-4">
        <h2 className="text-lg font-semibold mb-3">Existing Plans</h2>
        {isLoading ? (
          <div>Loading fee plans...</div>
        ) : isError ? (
          <div className="text-red-600 text-sm">Failed to load fee plans.</div>
        ) : plans.length === 0 ? (
          <div className="text-sm text-slate-600">No fee plans found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">ID</th>
                  <th className="p-2 text-left">Name</th>
                  <th className="p-2 text-left">Academic Year</th>
                  <th className="p-2 text-left">Frequency</th>
                  <th className="p-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {plans.map((p: any) => {
                  const isEditing = editingId === p.id;
                  return (
                    <tr key={p.id} className="border-t">
                      <td className="p-2">{p.id}</td>
                      <td className="p-2">
                        {isEditing ? (
                          <input
                            value={editingName}
                            onChange={(e) => setEditingName(e.target.value)}
                            className="border rounded px-2 py-1 text-sm w-full"
                          />
                        ) : (
                          <Link
                            to={`/fee-plans/${p.id}`}
                            className="text-blue-600 hover:underline"
                          >
                            {p.name}
                          </Link>
                        )}
                      </td>
                      <td className="p-2">
                        {isEditing ? (
                          <input
                            value={editingYear}
                            onChange={(e) => setEditingYear(e.target.value)}
                            className="border rounded px-2 py-1 text-sm w-full"
                          />
                        ) : (
                          p.academic_year
                        )}
                      </td>
                      <td className="p-2">
                        {isEditing ? (
                          <select
                            value={editingFrequency}
                            onChange={(e) =>
                              setEditingFrequency(e.target.value)
                            }
                            className="border rounded px-2 py-1 text-sm"
                          >
                            <option value="monthly">Monthly</option>
                            <option value="termly">Termly</option>
                            <option value="yearly">Yearly</option>
                          </select>
                        ) : (
                          p.frequency
                        )}
                      </td>
                      <td className="p-2 text-right space-x-2">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => saveEdit(p.id)}
                              disabled={(updateMutation as any).isPending}
                              className="px-3 py-1 rounded bg-green-600 text-white text-xs disabled:opacity-60"
                            >
                              {(updateMutation as any).isPending
                                ? "Saving..."
                                : "Save"}
                            </button>
                            <button
                              type="button"
                              onClick={cancelEditing}
                              disabled={(updateMutation as any).isPending}
                              className="px-3 py-1 rounded bg-slate-200 text-slate-800 text-xs disabled:opacity-60"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => startEditing(p)}
                              className="px-3 py-1 rounded bg-slate-200 text-slate-800 text-xs"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDelete(p.id)}
                              disabled={(deleteMutation as any).isPending}
                              className="px-3 py-1 rounded bg-red-600 text-white text-xs disabled:opacity-60"
                            >
                              {(deleteMutation as any).isPending
                                ? "Deleting..."
                                : "Delete"}
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
