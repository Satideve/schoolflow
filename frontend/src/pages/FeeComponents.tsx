/* C:\coding_projects\dev\schoolflow\frontend\src\pages\FeeComponents.tsx */
import React from "react";
import { useForm } from "react-hook-form";
import { useFeeComponents, useCreateFeeComponent } from "../api/queries";
import { useToast } from "../components/ui/use-toast";

type FormValues = {
  name: string;
  description: string;
};

export default function FeeComponents() {
  const { data, isLoading, isError } = useFeeComponents();
  const createMutation = useCreateFeeComponent();
  const { register, handleSubmit, reset } = useForm<FormValues>();
  const toast = useToast();

  const components = Array.isArray(data) ? data : data ?? [];

  const onSubmit = async (values: FormValues) => {
    try {
      await createMutation.mutateAsync({
        name: values.name.trim(),
        description: values.description.trim() || undefined,
      });
      reset();
      try {
        toast.push(`Fee component created: ${values.name}`);
      } catch {
        console.log("Fee component created");
      }
    } catch (err) {
      console.error("create fee component failed", err);
      try {
        toast.push("Create fee component failed");
      } catch {
        console.log("Create fee component failed");
      }
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Fee Components</h1>

      <div className="bg-white rounded shadow p-4">
        <h2 className="text-lg font-semibold mb-3">Add Fee Component</h2>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex flex-col gap-3 max-w-md"
        >
          <input
            {...register("name", { required: true })}
            placeholder="Name (e.g., Tuition, Transport)"
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            {...register("description")}
            placeholder="Description (optional)"
            className="border rounded px-3 py-2 text-sm"
          />
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
        <h2 className="text-lg font-semibold mb-3">Existing Components</h2>
        {isLoading ? (
          <div>Loading fee components...</div>
        ) : isError ? (
          <div className="text-red-600 text-sm">
            Failed to load fee components.
          </div>
        ) : components.length === 0 ? (
          <div className="text-sm text-slate-600">No fee components found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">ID</th>
                  <th className="p-2 text-left">Name</th>
                  <th className="p-2 text-left">Description</th>
                </tr>
              </thead>
              <tbody>
                {components.map((c: any) => (
                  <tr key={c.id} className="border-t">
                    <td className="p-2">{c.id}</td>
                    <td className="p-2">{c.name}</td>
                    <td className="p-2">{c.description ?? "-"}</td>
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
