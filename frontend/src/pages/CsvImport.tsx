/* C:\coding_projects\dev\schoolflow\frontend\src\pages\CsvImport.tsx */
import React, { useState } from "react";
import {
  uploadClassSectionsCsv,
  uploadStudentsCsv,
  uploadFeePlansCsv,
} from "../api/adminCsv";

type UploadState = "idle" | "uploading" | "success" | "error";

function SectionUpload(props: {
  title: string;
  description: string;
  onUpload: (file: File) => Promise<any>;
}) {
  const { title, description, onUpload } = props;
  const [state, setState] = useState<UploadState>("idle");
  const [message, setMessage] = useState<string>("");
  const [fileName, setFileName] = useState<string>("");

  async function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setState("uploading");
    setMessage("");

    try {
      await onUpload(file);
      setState("success");
      setMessage("Upload successful.");
    } catch (err: any) {
      console.error("CSV upload failed", err);
      setState("error");
      setMessage("Upload failed. See console for details.");
    } finally {
      e.target.value = "";
    }
  }

  return (
    <div className="bg-white rounded shadow p-4 space-y-2">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-sm text-slate-600">{description}</p>
      <div className="flex items-center gap-3">
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={handleChange}
          className="text-sm"
        />
        {fileName && (
          <span className="text-xs text-slate-500 truncate max-w-[200px]">
            Last: {fileName}
          </span>
        )}
      </div>
      {state !== "idle" && (
        <div className="text-xs">
          {state === "uploading" && (
            <span className="text-blue-600">Uploading...</span>
          )}
          {state === "success" && (
            <span className="text-green-600">{message}</span>
          )}
          {state === "error" && (
            <span className="text-red-600">{message}</span>
          )}
        </div>
      )}
    </div>
  );
}

const CsvImport: React.FC = () => {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold mb-2">CSV Import (Admin)</h1>
      <p className="text-sm text-slate-600 mb-4">
        Use these tools to bulk-import master data. Only admin-like roles
        should see and use this page.
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        <SectionUpload
          title="Class Sections"
          description="Upload class_sections.csv (columns: name, academic_year, other columns ignored)."
          onUpload={uploadClassSectionsCsv}
        />

        <SectionUpload
          title="Students"
          description="Upload students.csv (columns: name, roll_number, class_section_id, other columns ignored)."
          onUpload={uploadStudentsCsv}
        />

        <SectionUpload
          title="Fee Plans & Components"
          description="Upload seed_fees.csv (columns: fee_plan_name, academic_year, frequency, component_name, amount, is_mandatory)."
          onUpload={uploadFeePlansCsv}
        />
      </div>
    </div>
  );
};

export default CsvImport;
