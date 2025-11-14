/* C:\coding_projects\dev\schoolflow\frontend\src\utils\currency.ts */
export function formatINR(amount: number | string) {
  const n = typeof amount === "string" ? Number(amount) : amount;
  if (isNaN(n)) return "-";
  return n.toLocaleString("en-IN", { style: "currency", currency: "INR" });
}
