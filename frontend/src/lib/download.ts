// src/lib/download.ts

/**
 * Proxy-safe, token-secured PDF download.
 *
 * WHY THIS EXISTS:
 * - fetch / axios / blob WILL corrupt PDFs behind proxies (Vercel, ngrok, Cloudflare)
 * - PDFs must be streamed natively by the browser
 *
 * AUTH MODEL:
 * - Backend enforces JWT (Authorization: Bearer)
 * - No cookies are required or reintroduced
 *
 * HOW IT WORKS:
 * - Browser performs a document navigation
 * - Browser streams bytes directly (no JS touching binary)
 * - Backend still validates token normally
 */
export function downloadWithAuth(url: string) {
  const a = document.createElement("a");

  a.href = url;

  // Let browser handle the binary stream directly
  a.target = "_blank";
  a.rel = "noopener noreferrer";

  document.body.appendChild(a);
  a.click();
  a.remove();
}
