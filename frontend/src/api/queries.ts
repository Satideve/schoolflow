/* C:\coding_projects\dev\schoolflow\frontend\src\api\queries.ts */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import type {
  InvoiceCreateDTO,
  Invoice,
  Receipt,
  FeeAssignment,
  FeeAssignmentCreateDTO,
  Student,
  FeePlan,
} from "../types/api";

/* ------------------------------------------------------
   LIST INVOICES
------------------------------------------------------- */
export function useInvoices() {
  return useQuery({
    queryKey: ["invoices"],
    queryFn: async (): Promise<Invoice[]> => {
      const { data } = await api.get("/api/v1/invoices/");
      return data;
    },
  });
}

/* ------------------------------------------------------
   GET SINGLE INVOICE
------------------------------------------------------- */
export function useInvoice(id?: number | string) {
  return useQuery({
    queryKey: ["invoice", id],
    queryFn: async (): Promise<Invoice> => {
      const { data } = await api.get(`/api/v1/invoices/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

/* ------------------------------------------------------
   CREATE INVOICE
------------------------------------------------------- */
export function useCreateInvoice() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: InvoiceCreateDTO): Promise<Invoice> => {
      const { data } = await api.post("/api/v1/invoices/", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
    },
  });
}

/* ------------------------------------------------------
   LIST RECEIPTS
------------------------------------------------------- */
export function useReceipts() {
  return useQuery({
    queryKey: ["receipts"],
    queryFn: async (): Promise<Receipt[]> => {
      const { data } = await api.get("/api/v1/receipts/");
      return data;
    },
  });
}

/* ------------------------------------------------------
   STUDENTS
------------------------------------------------------- */

export function useStudents() {
  return useQuery({
    queryKey: ["students"],
    queryFn: async (): Promise<Student[]> => {
      const { data } = await api.get("/api/v1/students/");
      return data;
    },
  });
}

/* ------------------------------------------------------
   FEE PLANS
------------------------------------------------------- */

export function useFeePlans() {
  return useQuery({
    queryKey: ["fee-plans"],
    queryFn: async (): Promise<FeePlan[]> => {
      const { data } = await api.get("/api/v1/fee-plans/");
      return data;
    },
  });
}

/* ------------------------------------------------------
   FEE ASSIGNMENTS
------------------------------------------------------- */

export function useFeeAssignments(params?: {
  student_id?: number;
  fee_plan_id?: number;
}) {
  return useQuery({
    queryKey: ["fee-assignments", params ?? {}],
    queryFn: async (): Promise<FeeAssignment[]> => {
      const { data } = await api.get("/api/v1/fee-assignments", {
        params,
      });
      return data;
    },
  });
}

export function useCreateFeeAssignment() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (
      payload: FeeAssignmentCreateDTO
    ): Promise<FeeAssignment> => {
      const { data } = await api.post("/api/v1/fee-assignments", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-assignments"] });
    },
  });
}
