/* C:\coding_projects\dev\schoolflow\frontend\src\pages\Students.tsx */
import React from "react";
import { useStudents, useClassSections, useCreateStudent } from "../api/queries";
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
  const { register, handleSubmit, reset } = useForm<FormValues>();
  const toast = useToast();

  const sections = Array.isArray(sectionsData) ? sectionsData : sectionsData ?? [];
  const students = Array.isArray(studentsData) ? studentsData : studentsData ?? [];

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
                </tr>
              </thead>
              <tbody>
                {students.map((st: any) => (
                  <tr key={st.id} className="border-t">
                    <td className="p-2">{st.id}</td>
                    <td className="p-2">{st.name}</td>
                    <td className="p-2">{st.roll_number}</td>
                    <td className="p-2">{sectionLabel(st.class_section_id)}</td>
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
