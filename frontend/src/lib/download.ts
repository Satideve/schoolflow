// src/lib/download.ts

/**
 * Token-based, proxy-safe PDF download.
 *
 * DESIGN DECISIONS:
 * - Auth is strictly Bearer-token based (no cookies).
 * - Download uses fetch + blob so Authorization header is always sent.
 * - credentials: "omit" prevents proxy / CORS corruption.
 * - This works reliably on localhost, ngrok, and Vercel.
 */
export async function downloadWithAuth(
  url: string,
  filename: string,
) {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("Not authenticated");
  }

  const res = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    credentials: "omit", // 🔒 critical: no cookies, no proxy mutation
    mode: "cors",
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Download failed: ${res.status} ${text}`);
  }

  const blob = await res.blob();

  // Defensive check (helps catch proxy/auth issues early)
  if (blob.size < 100) {
    throw new Error("Downloaded file is invalid or empty");
  }

  const blobUrl = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;

  document.body.appendChild(a);
  a.click();
  a.remove();

  // Delay revocation for slower environments (Vercel)
  setTimeout(() => {
    window.URL.revokeObjectURL(blobUrl);
  }, 1000);
}
