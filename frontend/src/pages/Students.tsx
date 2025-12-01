/* C:\coding_projects\dev\schoolflow\frontend\src\pages\Students.tsx */
import React from "react";
import {
  useStudents,
  useClassSections,
  useCreateStudent,
  useUpdateStudent,
  useDeleteStudent,
} from "../api/queries";
import { useForm } from "react-hook-form";
import { useToast } from "../components/ui/use-toast";

type FormValues = {
  name: string;
  roll_number: string;
  class_section_id: string;
};

export default function Students() {
  const { data: studentsData, isLoading, isError } = useStudents();
  const { data: sectionsData } = useClassSections();
  const createMutation = useCreateStudent();
  const updateMutation = useUpdateStudent();
  const deleteMutation = useDeleteStudent();
  const { register, handleSubmit, reset } = useForm<FormValues>();
  const toast = useToast();

  const sections = Array.isArray(sectionsData) ? sectionsData : sectionsData ?? [];
  const students = Array.isArray(studentsData) ? studentsData : studentsData ?? [];

  // Local state for inline editing
  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [editName, setEditName] = React.useState<string>("");
  const [editRoll, setEditRoll] = React.useState<string>("");
  const [editSectionId, setEditSectionId] = React.useState<string>("");

  const onSubmit = async (values: FormValues) => {
    try {
      await createMutation.mutateAsync({
        name: values.name.trim(),
        roll_number: values.roll_number.trim(),
        class_section_id: Number(values.class_section_id),
      });
      reset();
      try {
        toast.push(`Student created: ${values.name} (${values.roll_number})`);
      } catch {
        console.log("Student created");
      }
    } catch (err) {
      console.error("create student failed", err);
      try {
        toast.push("Create student failed");
      } catch {
        console.log("Create student failed");
      }
    }
  };

  function sectionLabel(id: number | undefined) {
    if (!id) return "-";
    const sec = sections.find((s: any) => s.id === id);
    return sec ? `${sec.name} (${sec.academic_year})` : `#${id}`;
  }

  const startEditing = (st: any) => {
    setEditingId(st.id);
    setEditName(st.name ?? "");
    setEditRoll(st.roll_number ?? "");
    setEditSectionId(st.class_section_id ? String(st.class_section_id) : "");
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditName("");
    setEditRoll("");
    setEditSectionId("");
  };

  const saveEditing = async (id: number) => {
    const name = editName.trim();
    const roll = editRoll.trim();
    const class_section_id = editSectionId ? Number(editSectionId) : undefined;

    if (!name || !roll || !class_section_id) {
      try {
        toast.push("Name, roll number, and class section are required.");
      } catch {
        console.log("Name, roll number, and class section are required.");
      }
      return;
    }

    try {
      await updateMutation.mutateAsync({
        id,
        name,
        roll_number: roll,
        class_section_id,
      });
      cancelEditing();
      try {
        toast.push("Student updated.");
      } catch {
        console.log("Student updated.");
      }
    } catch (err: any) {
      console.error("update student failed", err);
      let msg = "Update student failed.";
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

  const deleteStudent = async (id: number) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this student?"
    );
    if (!confirmed) return;

    try {
      await deleteMutation.mutateAsync(id);
      try {
        toast.push("Student deleted.");
      } catch {
        console.log("Student deleted.");
      }
    } catch (err: any) {
      console.error("delete student failed", err);
      let msg = "Delete student failed.";
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
      <h1 className="text-2xl font-bold">Students</h1>

      <div className="bg-white rounded shadow p-4">
        <h2 className="text-lg font-semibold mb-3">Add Student</h2>
        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex flex-col gap-3 max-w-md"
        >
          <input
            {...register("name", { required: true })}
            placeholder="Name"
            className="border rounded px-3 py-2 text-sm"
          />
          <input
            {...register("roll_number", { required: true })}
            placeholder="Roll number (e.g., 1A-001)"
            className="border rounded px-3 py-2 text-sm"
          />
          <select
            {...register("class_section_id", { required: true })}
            className="border rounded px-3 py-2 text-sm"
            defaultValue=""
          >
            <option value="" disabled>
              Select class section
            </option>
            {sections.map((s: any) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.academic_year})
              </option>
            ))}
          </select>

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={(createMutation as any).isPending}
              className="inline-flex items-center justify-center px-4 py-2 rounded bg-blue-600 text-white text-sm disabled:opacity-60"
            >
              {(createMutation as any).isPending ? "Saving..." : "Create"}
            </button>

            {/* DEBUG: Test Toast button */}
            <button
              type="button"
              onClick={() => {
                try {
                  toast.push("Test toast from Students page");
                } catch (err) {
                  console.error("toast.push failed", err);
                }
              }}
              className="inline-flex items-center justify-center px-3 py-2 rounded bg-slate-800 text-white text-xs"
            >
              Test Toast
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white rounded shadow p-4">
        <h2 className="text-lg font-semibold mb-3">Existing Students</h2>
        {isLoading ? (
          <div>Loading students...</div>
        ) : isError ? (
          <div className="text-red-600 text-sm">Failed to load students.</div>
        ) : students.length === 0 ? (
          <div className="text-sm text-slate-600">No students found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">ID</th>
                  <th className="p-2 text-left">Name</th>
                  <th className="p-2 text-left">Roll Number</th>
                  <th className="p-2 text-left">Class Section</th>
                  <th className="p-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {students.map((st: any) => {
                  const isEditing = editingId === st.id;
                  return (
                    <tr key={st.id} className="border-t">
                      <td className="p-2">{st.id}</td>
                      <td className="p-2">
                        {isEditing ? (
                          <input
                            className="border rounded px-2 py-1 text-sm w-full"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                          />
                        ) : (
                          st.name
                        )}
                      </td>
                      <td className="p-2">
                        {isEditing ? (
                          <input
                            className="border rounded px-2 py-1 text-sm w-full"
                            value={editRoll}
                            onChange={(e) => setEditRoll(e.target.value)}
                          />
                        ) : (
                          st.roll_number
                        )}
                      </td>
                      <td className="p-2">
                        {isEditing ? (
                          <select
                            className="border rounded px-2 py-1 text-sm w-full"
                            value={editSectionId}
                            onChange={(e) => setEditSectionId(e.target.value)}
                          >
                            <option value="">Select class section</option>
                            {sections.map((s: any) => (
                              <option key={s.id} value={s.id}>
                                {s.name} ({s.academic_year})
                              </option>
                            ))}
                          </select>
                        ) : (
                          sectionLabel(st.class_section_id)
                        )}
                      </td>
                      <td className="p-2 text-right space-x-2">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => saveEditing(st.id)}
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
                              onClick={() => startEditing(st)}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-slate-200 text-slate-800 text-xs"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => deleteStudent(st.id)}
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
