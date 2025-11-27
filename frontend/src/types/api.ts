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
  role?: "admin" | "clerk" | string;
};

export type Student = {
  id: number;
  name?: string;
  admission_no?: string;
  class_section_id?: number;
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

/* -----------------------------
   Fee Plans
------------------------------ */

export type FeePlan = {
  id: number;
  name: string;
  academic_year: string;
  frequency: string;
};

/* -----------------------------
   Fee Assignments
------------------------------ */

export type FeeAssignment = {
  id: number;
  student_id: number;
  fee_plan_id: number;
  invoice_id?: number | null;
  concession: string; // backend returns Decimal as string, e.g. "0.00"
  note?: string | null;
};

export type FeeAssignmentCreateDTO = {
  student_id: number;
  fee_plan_id: number;
  invoice_id?: number | null;
  concession?: number | null;
  note?: string | null;
};
