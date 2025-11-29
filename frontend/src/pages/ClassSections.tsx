/* C:\coding_projects\dev\schoolflow\frontend\src\pages\ClassSections.tsx */
import React from "react";
import { useClassSections, useCreateClassSection } from "../api/queries";
import { useForm } from "react-hook-form";
import { useToast } from "../components/ui/use-toast";

type FormValues = {
  name: string;
  academic_year: string;
};

export default function ClassSections() {
  const { data, isLoading, isError } = useClassSections();
  const createMutation = useCreateClassSection();
  const { register, handleSubmit, reset } = useForm<FormValues>();
  const toast = useToast(); // your hook exposes .push(msg)

  const onSubmit = async (values: FormValues) => {
    try {
      await createMutation.mutateAsync({
        name: values.name.trim(),
        academic_year: values.academic_year.trim(),
      });
      reset();
      try {
        toast.push(`Class section created: ${values.name} (${values.academic_year})`);
      } catch {
        console.log("Class section created");
      }
    } catch (err) {
      console.error("create class section failed", err);
      try {
        toast.push("Create class section failed");
      } catch {
        console.log("Create class section failed");
      }
    }
  };

  const sections = Array.isArray(data) ? data : data ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Class Sections</h1>

      <div className="bg-white rounded shadow p-4">
        <h2 className="text-lg font-semibold mb-3">Add Class Section</h2>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex flex-col gap-3 max-w-md"
        >
          <input
            {...register("name", { required: true })}
            placeholder="Name (e.g., IX-A)"
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            {...register("academic_year", { required: true })}
            placeholder="Academic Year (e.g., 2025-2026)"
            className="border rounded px-3 py-2 text-sm"
          />
          <button
            type="submit"
            // React Query v4 uses isPending, not isLoading
            disabled={(createMutation as any).isPending}
            className="inline-flex items-center justify-center px-4 py-2 rounded bg-blue-600 text-white text-sm disabled:opacity-60"
          >
            {(createMutation as any).isPending ? "Saving..." : "Create"}
          </button>
        </form>
      </div>

      <div className="bg-white rounded shadow p-4">
        <h2 className="text-lg font-semibold mb-3">Existing Sections</h2>
        {isLoading ? (
          <div>Loading class sections...</div>
        ) : isError ? (
          <div className="text-red-600 text-sm">Failed to load class sections.</div>
        ) : sections.length === 0 ? (
          <div className="text-sm text-slate-600">No class sections found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">ID</th>
                  <th className="p-2 text-left">Name</th>
                  <th className="p-2 text-left">Academic Year</th>
                </tr>
              </thead>
              <tbody>
                {sections.map((s: any) => (
                  <tr key={s.id} className="border-t">
                    <td className="p-2">{s.id}</td>
                    <td className="p-2">{s.name}</td>
                    <td className="p-2">{s.academic_year}</td>
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
