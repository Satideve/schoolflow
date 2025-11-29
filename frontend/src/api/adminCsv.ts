/* C:\coding_projects\dev\schoolflow\frontend\src\api\adminCsv.ts */
import api from "./client";

export async function uploadClassSectionsCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post(
    "/api/v1/admin/csv/class-sections",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return data;
}

export async function uploadStudentsCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post(
    "/api/v1/admin/csv/students",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return data;
}

export async function uploadFeePlansCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await api.post(
    "/api/v1/admin/csv/fee-plans",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return data;
}
