/* C:\coding_projects\dev\schoolflow\frontend\src\api\queries.ts */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import {
  InvoiceCreateDTO,
  Invoice,
  Receipt,
  ClassSection,
  Student,
  FeeComponent,
  FeePlan,
} from "../types/api";

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

export function useCreateStudent() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      name: string;
      roll_number: string;
      class_section_id: number;
    }): Promise<Student> => {
      const { data } = await api.post("/api/v1/students/", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
    },
  });
}

/* ------------------------------------------------------
   CLASS SECTIONS
------------------------------------------------------- */
export function useClassSections() {
  return useQuery({
    queryKey: ["class-sections"],
    queryFn: async (): Promise<ClassSection[]> => {
      const { data } = await api.get("/api/v1/class-sections/");
      return data;
    },
  });
}

export function useCreateClassSection() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      name: string;
      academic_year: string;
    }): Promise<ClassSection> => {
      const { data } = await api.post("/api/v1/class-sections/", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["class-sections"] });
    },
  });
}

/* ------------------------------------------------------
   FEE COMPONENTS
------------------------------------------------------- */
export function useFeeComponents() {
  return useQuery({
    queryKey: ["fee-components"],
    queryFn: async (): Promise<FeeComponent[]> => {
      const { data } = await api.get("/api/v1/fee-components/");
      return data;
    },
  });
}

export function useCreateFeeComponent() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      name: string;
      description?: string | null;
    }): Promise<FeeComponent> => {
      const { data } = await api.post("/api/v1/fee-components/", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-components"] });
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

export function useCreateFeePlan() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      name: string;
      academic_year: string;
      frequency: string;
    }): Promise<FeePlan> => {
      const { data } = await api.post("/api/v1/fee-plans/", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-plans"] });
    },
  });
}

/* ------------------------------------------------------
   FEE ASSIGNMENTS
------------------------------------------------------- */
export function useFeeAssignments() {
  return useQuery({
    queryKey: ["fee-assignments"],
    queryFn: async (): Promise<any[]> => {
      const { data } = await api.get("/api/v1/fee-assignments");
      return data;
    },
  });
}

export function useCreateFeeAssignment() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      student_id: number;
      fee_plan_id: number;
      invoice_id?: number | null;
      concession?: number;
      note?: string;
    }): Promise<any> => {
      const { data } = await api.post("/api/v1/fee-assignments", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-assignments"] });
    },
  });
}

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
