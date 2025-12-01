/* C:\coding_projects\dev\schoolflow\frontend\src\types\api.ts */

/**
 * Keep these field names identical to backend schema names.
 * Extend as needed.
 */

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type User = {
  id: number;
  email: string;
  full_name?: string | null;
  role?: "admin" | "clerk" | "student" | string;
  // NEW: optional mapping to a Student row (for student/parent accounts)
  student_id?: number | null;
};

export type ClassSection = {
  id: number;
  name: string;
  academic_year: string;
};

export type Student = {
  id: number;
  name?: string;
  roll_number?: string;
  class_section_id?: number;
};

export type FeeComponent = {
  id: number;
  name: string;
  description?: string | null;
};

export type FeePlan = {
  id: number;
  name: string;
  academic_year: string;
  frequency: string;
};

/**
 * One line item (component) within a fee plan.
 * This matches the fee_plan_component backend schema.
 */
export type FeePlanComponent = {
  id: number;
  fee_plan_id: number;
  fee_component_id: number;
  amount: number;
  // Often the backend will return the linked component for convenience.
  fee_component?: FeeComponent | null;
};

export type InvoiceItem = {
  title: string;
  description?: string | null;
  amount: number;
};

export type Invoice = {
  id: number;
  invoice_no: string;
  student_id: number;
  student?: Student | null;
  period?: string | null;
  due_date?: string | null;
  created_at?: string | null;
  items: InvoiceItem[];
  items_total: number;
  total_due: number;
  paid_amount: number;
  balance: number;
};

export type InvoiceCreateDTO = {
  invoice_no: string;
  student_id: number;
  period: string;
  due_date: string;
  amount_due?: number | null;
};

export type Receipt = {
  id: number;
  receipt_no: string;
  invoice_id: number;
  amount: number;
  created_at?: string | null;
};

/**
 * Fee assignment linking a student to a fee plan (optionally to an invoice),
 * with optional concession and note.
 * Matches backend FeeAssignmentOut schema.
 */
export type FeeAssignment = {
  id: number;
  student_id: number;
  fee_plan_id: number;
  invoice_id?: number | null;
  concession?: number | null;
  note?: string | null;
};
