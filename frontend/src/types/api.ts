/* C:\coding_projects\dev\schoolflow\frontend\src\types\api.ts */
export type User = {
  id: number;
  email: string;
  role: "admin" | "clerk" | string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type InvoiceItem = {
  title: string;
  amount: number;
  qty?: number;
};

export type Invoice = {
  id: number;
  invoice_no: string;
  student_id: number;
  student?: any;
  period: string;
  due_date?: string;
  created_at?: string;
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
  due_date?: string;
  amount_due?: number;
  items?: InvoiceItem[];
};

export type Receipt = {
  id: number;
  receipt_no: string;
  invoice_id: number;
  amount: number;
  created_at: string;
};
