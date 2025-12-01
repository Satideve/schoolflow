/* C:\coding_projects\dev\schoolflow\frontend\src\pages\FeeAssignments.tsx */
import React, { useState, useMemo } from "react";
import {
  useStudents,
  useFeePlans,
  useFeeAssignments,
  useCreateFeeAssignment,
  useUpdateFeeAssignment,
  useDeleteFeeAssignment,
} from "../api/queries";
import { useToast } from "../components/ui/use-toast";
import type { FeeAssignment } from "../types/api";

type FormState = {
  student_id: string;
  fee_plan_id: string;
  concession: string;
  note: string;
};

export default function FeeAssignments() {
  const { data: students, isLoading: loadingStudents } = useStudents();
  const { data: feePlans, isLoading: loadingPlans } = useFeePlans();
  const {
    data: assignmentsData,
    isLoading: loadingAssignments,
  } = useFeeAssignments();
  const createAssignment = useCreateFeeAssignment();
  const updateAssignment = useUpdateFeeAssignment();
  const deleteAssignment = useDeleteFeeAssignment();
  const toast = useToast();

  const [form, setForm] = useState<FormState>({
    student_id: "",
    fee_plan_id: "",
    concession: "",
    note: "",
  });

  // Local state for inline editing
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editConcession, setEditConcession] = useState<string>("");
  const [editNote, setEditNote] = useState<string>("");

  const studentNameById = useMemo(() => {
    const map = new Map<number, string>();
    (students ?? []).forEach((s: any) => {
      if (s && typeof s.id === "number") {
        map.set(s.id, s.name ?? `Student #${s.id}`);
      }
    });
    return map;
  }, [students]);

  const feePlanNameById = useMemo(() => {
    const map = new Map<number, string>();
    (feePlans ?? []).forEach((p: any) => {
      if (p && typeof p.id === "number") {
        const label = p.name
          ? `${p.name} (${p.academic_year})`
          : `Plan #${p.id}`;
        map.set(p.id, label);
      }
    });
    return map;
  }, [feePlans]);

  const handleChange = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit: React.FormEventHandler = async (e) => {
    e.preventDefault();
    if (!form.student_id || !form.fee_plan_id) {
      return;
    }

    const payload = {
      student_id: Number(form.student_id),
      fee_plan_id: Number(form.fee_plan_id),
      concession: form.concession ? Number(form.concession) : undefined,
      note: form.note || undefined,
    };

    try {
      await createAssignment.mutateAsync(payload);
      try {
        toast.push("Fee assignment created");
      } catch {
        console.log("Fee assignment created");
      }
      setForm({
        student_id: "",
        fee_plan_id: "",
        concession: "",
        note: "",
      });
    } catch (err) {
      console.error("Create fee assignment failed", err);
      try {
        toast.push("Create fee assignment failed");
      } catch {
        console.log("Create fee assignment failed");
      }
    }
  };

  const list: FeeAssignment[] = Array.isArray(assignmentsData)
    ? assignmentsData
    : (assignmentsData ?? []);

  const startEditing = (a: FeeAssignment) => {
    setEditingId(a.id);
    setEditConcession(
      a.concession !== null && a.concession !== undefined
        ? String(a.concession)
        : ""
    );
    setEditNote(a.note ?? "");
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditConcession("");
    setEditNote("");
  };

  const saveEditing = async (id: number) => {
    const concession =
      editConcession.trim() !== "" ? Number(editConcession) : undefined;
    const note = editNote.trim() !== "" ? editNote.trim() : undefined;

    try {
      await updateAssignment.mutateAsync({
        id,
        concession,
        note,
      });
      cancelEditing();
      try {
        toast.push("Fee assignment updated");
      } catch {
        console.log("Fee assignment updated");
      }
    } catch (err) {
      console.error("Update fee assignment failed", err);
      try {
        toast.push("Update fee assignment failed");
      } catch {
        console.log("Update fee assignment failed");
      }
    }
  };

  const deleteAssignmentRow = async (id: number) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this assignment?"
    );
    if (!confirmed) return;

    try {
      await deleteAssignment.mutateAsync(id);
      try {
        toast.push("Fee assignment deleted");
      } catch {
        console.log("Fee assignment deleted");
      }
    } catch (err: any) {
      console.error("Delete fee assignment failed", err);
      let msg = "Delete fee assignment failed";
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
      <h2 className="text-xl font-semibold mb-2">Fee Assignments</h2>

      <section className="bg-white rounded shadow p-4 space-y-4">
        <h3 className="font-medium">Create Assignment</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm mb-1">Student</label>
              <select
                className="w-full border rounded p-2"
                value={form.student_id}
                onChange={(e) => handleChange("student_id", e.target.value)}
                disabled={loadingStudents}
              >
                <option value="">Select student</option>
                {students?.map((s: any) => (
                  <option key={s.id} value={s.id}>
                    {s.name ?? `Student #${s.id}`}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1">Fee Plan</label>
              <select
                className="w-full border rounded p-2"
                value={form.fee_plan_id}
                onChange={(e) => handleChange("fee_plan_id", e.target.value)}
                disabled={loadingPlans}
              >
                <option value="">Select fee plan</option>
                {feePlans?.map((p: any) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.academic_year})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-sm mb-1">
                Concession (optional)
              </label>
              <input
                type="number"
                step="0.01"
                className="w-full border rounded p-2"
                value={form.concession}
                onChange={(e) => handleChange("concession", e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm mb-1">Note (optional)</label>
              <input
                type="text"
                className="w-full border rounded p-2"
                value={form.note}
                onChange={(e) => handleChange("note", e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            className="mt-2 px-4 py-2 rounded bg-green-600 text-white disabled:opacity-60"
            disabled={(createAssignment as any).isPending}
          >
            {(createAssignment as any).isPending ? "Saving..." : "Assign Plan"}
          </button>
        </form>
      </section>

      <section className="bg-white rounded shadow p-4">
        <h3 className="font-medium mb-3">Existing Assignments</h3>
        {loadingAssignments ? (
          <div className="text-sm text-gray-500">Loading assignments...</div>
        ) : !list || list.length === 0 ? (
          <div className="text-sm text-gray-500">No assignments yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 pr-2">ID</th>
                  <th className="text-left py-2 pr-2">Student</th>
                  <th className="text-left py-2 pr-2">Fee Plan</th>
                  <th className="text-left py-2 pr-2">Concession</th>
                  <th className="text-left py-2 pr-2">Note</th>
                  <th className="text-right py-2 pl-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {list.map((a) => {
                  const isEditing = editingId === a.id;
                  return (
                    <tr key={a.id} className="border-b last:border-b-0">
                      <td className="py-1 pr-2">{a.id}</td>
                      <td className="py-1 pr-2">
                        {studentNameById.get(a.student_id) ??
                          `Student #${a.student_id}`}
                      </td>
                      <td className="py-1 pr-2">
                        {feePlanNameById.get(a.fee_plan_id) ??
                          `Plan #${a.fee_plan_id}`}
                      </td>
                      <td className="py-1 pr-2">
                        {isEditing ? (
                          <input
                            type="number"
                            step="0.01"
                            className="w-full border rounded p-1"
                            value={editConcession}
                            onChange={(e) =>
                              setEditConcession(e.target.value)
                            }
                          />
                        ) : (
                          a.concession ?? ""
                        )}
                      </td>
                      <td className="py-1 pr-2">
                        {isEditing ? (
                          <input
                            type="text"
                            className="w-full border rounded p-1"
                            value={editNote}
                            onChange={(e) => setEditNote(e.target.value)}
                          />
                        ) : (
                          a.note ?? ""
                        )}
                      </td>
                      <td className="py-1 pl-2 text-right space-x-2">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => saveEditing(a.id)}
                              disabled={(updateAssignment as any).isPending}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-green-600 text-white text-xs disabled:opacity-60"
                            >
                              {(updateAssignment as any).isPending
                                ? "Saving..."
                                : "Save"}
                            </button>
                            <button
                              type="button"
                              onClick={cancelEditing}
                              disabled={(updateAssignment as any).isPending}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-slate-300 text-slate-800 text-xs disabled:opacity-60"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => startEditing(a)}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-slate-200 text-slate-800 text-xs"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => deleteAssignmentRow(a.id)}
                              disabled={(deleteAssignment as any).isPending}
                              className="inline-flex items-center justify-center px-3 py-1 rounded bg-red-600 text-white text-xs disabled:opacity-60"
                            >
                              {(deleteAssignment as any).isPending
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
      </section>
    </div>
  );
}
