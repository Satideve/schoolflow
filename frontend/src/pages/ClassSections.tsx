/* C:\coding_projects\dev\schoolflow\frontend\src\pages\ClassSections.tsx */
import React from "react";
import {
  useClassSections,
  useCreateClassSection,
  useUpdateClassSection,
  useDeleteClassSection,
} from "../api/queries";
import { useForm } from "react-hook-form";
import { useToast } from "../components/ui/use-toast";

type FormValues = {
  name: string;
  academic_year: string;
};

export default function ClassSections() {
  const { data, isLoading, isError } = useClassSections();
  const createMutation = useCreateClassSection();
  const updateMutation = useUpdateClassSection();
  const deleteMutation = useDeleteClassSection();
  const { register, handleSubmit, reset } = useForm<FormValues>();
  const toast = useToast(); // your hook exposes .push(msg)

  const sections = Array.isArray(data) ? data : data ?? [];

  // Local state for inline editing
  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [editName, setEditName] = React.useState<string>("");
  const [editYear, setEditYear] = React.useState<string>("");

  const onSubmit = async (values: FormValues) => {
    try {
      await createMutation.mutateAsync({
        name: values.name.trim(),
        academic_year: values.academic_year.trim(),
      });
      reset();
      try {
        toast.push(
          `Class section created: ${values.name} (${values.academic_year})`
        );
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

  const startEditing = (section: any) => {
    setEditingId(section.id);
    setEditName(section.name ?? "");
    setEditYear(section.academic_year ?? "");
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditName("");
    setEditYear("");
  };

  const saveEditing = async (id: number) => {
    const name = editName.trim();
    const academic_year = editYear.trim();

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
      });
      cancelEditing();
      try {
        toast.push("Class section updated.");
      } catch {
        console.log("Class section updated.");
      }
    } catch (err) {
      console.error("update class section failed", err);
      try {
        toast.push("Update class section failed.");
      } catch {
        console.log("Update class section failed.");
      }
    }
  };

  const deleteSection = async (id: number) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this class section?"
    );
    if (!confirmed) return;

    try {
      await deleteMutation.mutateAsync(id);
      try {
        toast.push("Class section deleted.");
      } catch {
        console.log("Class section deleted.");
      }
    } catch (err: any) {
      console.error("delete class section failed", err);
      // Try to show backend error message if available
      let msg = "Delete class section failed.";
      const maybeResponse: any = err?.response;
      if (maybeResponse?.data?.detail) {
        if (typeof maybeResponse.data.detail === "string") {
          msg = maybeResponse.data.detail;
        } else if (typeof maybeResponse.data.detail === "object") {
          msg =
            maybeResponse.data.detail.message ||
            maybeResponse.data.detail.code ||
            msg;
        }
      }
      try {
        toast.push(msg);
      } catch {
        console.log(msg);
      }
    }
  };

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
          <div className="text-red-600 text-sm">
            Failed to load class sections.
          </div>
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
                  <th className="p-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sections.map((s: any) => {
                  const isEditing = editingId === s.id;
                  return (
                    <tr key={s.id} className="border-t">
                      <td className="p-2">{s.id}</td>
                      <td className="p-2">
                        {isEditing ? (
                          <input
                            className="border rounded px-2 py-1 text-sm w-full"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                          />
                        ) : (
                          s.name
                        )}
                      </td>
                      <td className="p-2">
                        {isEditing ? (
                          <input
                            className="border rounded px-2 py-1 text-sm w-full"
                            value={editYear}
                            onChange={(e) => setEditYear(e.target.value)}
                          />
                        ) : (
                          s.academic_year
                        )}
                      </td>
                      <td className="p-2 text-right space-x-2">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => saveEditing(s.id)}
                              disabled={(updateMutation as any).isPending}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-green-600 text-white text-xs disabled:opacity-60"
                            >
                              {(updateMutation as any).isPending
                                ? "Saving..."
                                : "Save"}
                            </button>
                            <button
                              type="button"
                              onClick={cancelEditing}
                              disabled={(updateMutation as any).isPending}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-slate-300 text-slate-800 text-xs disabled:opacity-60"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => startEditing(s)}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-slate-200 text-slate-800 text-xs"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => deleteSection(s.id)}
                              disabled={(deleteMutation as any).isPending}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-red-600 text-white text-xs disabled:opacity-60"
                            >
                              {(deleteMutation as any).isPending
                                ? "Removing..."
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
