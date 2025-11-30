/* C:\coding_projects\dev\schoolflow\frontend\src\pages\FeePlans.tsx */
import React from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { useFeePlans, useCreateFeePlan } from "../api/queries";
import { useToast } from "../components/ui/use-toast";

type FormValues = {
  name: string;
  academic_year: string;
  frequency: string;
};

export default function FeePlans() {
  const { data, isLoading, isError } = useFeePlans();
  const createMutation = useCreateFeePlan();
  const { register, handleSubmit, reset } = useForm<FormValues>({
    defaultValues: {
      frequency: "monthly",
    },
  });
  const toast = useToast();

  const plans = Array.isArray(data) ? data : data ?? [];

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

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Fee Plans</h1>

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
                </tr>
              </thead>
              <tbody>
                {plans.map((p: any) => (
                  <tr key={p.id} className="border-t">
                    <td className="p-2">{p.id}</td>
                    <td className="p-2">
                      <Link
                        to={`/fee-plans/${p.id}`}
                        className="text-blue-600 hover:underline"
                      >
                        {p.name}
                      </Link>
                    </td>
                    <td className="p-2">{p.academic_year}</td>
                    <td className="p-2">{p.frequency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
