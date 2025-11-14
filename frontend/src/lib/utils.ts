/* C:\coding_projects\dev\schoolflow\frontend\src\lib\utils.ts */
/**
 * Small utility helpers for the frontend
 */

/** classNames helper - joins truthy class strings */
export function cn(...args: Array<string | false | null | undefined>) {
  return args.filter(Boolean).join(" ");
}

/** format number as currency (INR style by default) */
export function formatMoney(value: number | string | null | undefined, currency = "INR") {
  const n = Number(value ?? 0);
  if (Number.isNaN(n)) return "-";
  try {
    // Use Intl if available; fallback to simple formatting
    return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(n);
  } catch (e) {
    return `${n.toFixed(2)}`;
  }
}
