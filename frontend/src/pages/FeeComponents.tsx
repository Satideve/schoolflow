/* C:\coding_projects\dev\schoolflow\frontend\src\pages\FeeComponents.tsx */
import React from "react";
import { useForm } from "react-hook-form";
import {
  useFeeComponents,
  useCreateFeeComponent,
  useUpdateFeeComponent,
  useDeleteFeeComponent,
} from "../api/queries";
import { useToast } from "../components/ui/use-toast";

type FormValues = {
  name: string;
  description: string;
};

export default function FeeComponents() {
  const { data, isLoading, isError } = useFeeComponents();
  const createMutation = useCreateFeeComponent();
  const updateMutation = useUpdateFeeComponent();
  const deleteMutation = useDeleteFeeComponent();
  const { register, handleSubmit, reset } = useForm<FormValues>();
  const toast = useToast();

  const components = Array.isArray(data) ? data : data ?? [];

  // Inline edit state
  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [editingName, setEditingName] = React.useState<string>("");
  const [editingDescription, setEditingDescription] =
    React.useState<string>("");

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

  const startEditing = (c: any) => {
    setEditingId(c.id);
    setEditingName(c.name ?? "");
    setEditingDescription(c.description ?? "");
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditingName("");
    setEditingDescription("");
  };

  const saveEdit = async (id: number) => {
    const name = editingName.trim();
    const description = editingDescription.trim() || undefined;

    if (!name) {
      try {
        toast.push("Name is required.");
      } catch {
        console.log("Name is required.");
      }
      return;
    }

    try {
      await updateMutation.mutateAsync({
        id,
        name,
        description,
      });
      cancelEditing();
      try {
        toast.push("Fee component updated.");
      } catch {
        console.log("Fee component updated.");
      }
    } catch (err) {
      console.error("update fee component failed", err);
      try {
        toast.push("Failed to update fee component.");
      } catch {
        console.log("Failed to update fee component.");
      }
    }
  };

  const handleDelete = async (id: number) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this fee component?"
    );
    if (!confirmed) return;

    try {
      await deleteMutation.mutateAsync(id);
      try {
        toast.push("Fee component deleted.");
      } catch {
        console.log("Fee component deleted.");
      }
    } catch (err) {
      console.error("delete fee component failed", err);
      try {
        toast.push("Failed to delete fee component.");
      } catch {
        console.log("Failed to delete fee component.");
      }
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Fee Components</h1>

      {/* Create form */}
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

      {/* List + edit/delete */}
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
                  <th className="p-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {components.map((c: any) => {
                  const isEditing = editingId === c.id;
                  return (
                    <tr key={c.id} className="border-t">
                      <td className="p-2">{c.id}</td>
                      <td className="p-2">
                        {isEditing ? (
                          <input
                            value={editingName}
                            onChange={(e) => setEditingName(e.target.value)}
                            className="border rounded px-2 py-1 text-sm w-full"
                          />
                        ) : (
                          c.name
                        )}
                      </td>
                      <td className="p-2">
                        {isEditing ? (
                          <input
                            value={editingDescription}
                            onChange={(e) =>
                              setEditingDescription(e.target.value)
                            }
                            className="border rounded px-2 py-1 text-sm w-full"
                          />
                        ) : (
                          c.description ?? "-"
                        )}
                      </td>
                      <td className="p-2 text-right space-x-2">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => saveEdit(c.id)}
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
                              onClick={() => startEditing(c)}
                              className="px-3 py-1 rounded bg-slate-200 text-slate-800 text-xs"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDelete(c.id)}
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
