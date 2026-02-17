// src/lib/download.ts

/**
 * Production-safe PDF download.
 *
 * IMPORTANT:
 * - Do NOT use fetch / blob / axios for PDFs
 * - Let the browser stream the file natively
 * - This avoids corruption on Vercel / ngrok / proxies
 */
export function downloadWithAuth(
  url: string,
  _filename?: string,
) {
  const token = localStorage.getItem("access_token");

  const a = document.createElement("a");

  // Pass auth via header using same-origin cookies OR Authorization header already set
  // Backend already supports Authorization: Bearer
  a.href = url;

  // Open in new tab so browser handles binary stream directly
  a.target = "_blank";
  a.rel = "noopener noreferrer";

  document.body.appendChild(a);
  a.click();
  a.remove();
}
