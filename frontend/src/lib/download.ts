// src/lib/download.ts
export async function downloadWithAuth(
  url: string,
  filename: string,
  token?: string,
) {
  const headers: Record<string, string> = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    headers,
    credentials: "omit",
    mode: "cors", // 🔒 force non-credentialed CORS
  });


  if (!res.ok) {
    throw new Error(`Download failed: ${res.status}`);
  }

  const blob = await res.blob();
  const blobUrl = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  a.remove();

  // Delay revocation to avoid race on slower environments (Vercel)
  setTimeout(() => {
    window.URL.revokeObjectURL(blobUrl);
  }, 1000);
}
