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
  FeePlanComponent,
  FeeAssignment,
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

/**
 * Update an existing student.
 */
export function useUpdateStudent() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      id: number;
      name?: string;
      roll_number?: string;
      class_section_id?: number;
    }): Promise<Student> => {
      const { id, ...body } = payload;
      const { data } = await api.patch(`/api/v1/students/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
    },
  });
}

/**
 * Delete a student.
 */
export function useDeleteStudent() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: number): Promise<void> => {
      await api.delete(`/api/v1/students/${id}`);
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

/**
 * Update an existing class section.
 */
export function useUpdateClassSection() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      id: number;
      name?: string;
      academic_year?: string;
    }): Promise<ClassSection> => {
      const { id, ...body } = payload;
      const { data } = await api.patch(`/api/v1/class-sections/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["class-sections"] });
    },
  });
}

/**
 * Delete a class section.
 */
export function useDeleteClassSection() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: number): Promise<void> => {
      await api.delete(`/api/v1/class-sections/${id}`);
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

/**
 * Get a single fee plan by ID
 */
export function useFeePlan(id?: number | string) {
  return useQuery({
    queryKey: ["fee-plan", id],
    queryFn: async (): Promise<FeePlan> => {
      const { data } = await api.get(`/api/v1/fee-plans/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

/* ------------------------------------------------------
   FEE PLAN COMPONENTS
------------------------------------------------------- */
/**
 * Fetch all fee plan components, and (optionally) filter by fee_plan_id.
 */
export function useFeePlanComponents(feePlanId?: number | string) {
  return useQuery({
    queryKey: ["fee-plan-components"],
    queryFn: async (): Promise<FeePlanComponent[]> => {
      const { data } = await api.get("/api/v1/fee-plan-components/");
      return data;
    },
    select: (components): FeePlanComponent[] => {
      if (!feePlanId) return components;
      const idStr = String(feePlanId);
      return components.filter((c) => String(c.fee_plan_id) === idStr);
    },
  });
}

/**
 * Create a new fee plan component (line item) for a plan.
 */
export function useCreateFeePlanComponent() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      fee_plan_id: number;
      fee_component_id: number;
      amount: number;
    }): Promise<FeePlanComponent> => {
      const { data } = await api.post("/api/v1/fee-plan-components/", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-plan-components"] });
    },
  });
}

/**
 * Update an existing fee plan component.
 */
export function useUpdateFeePlanComponent() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      id: number;
      fee_component_id?: number;
      amount?: number;
    }): Promise<FeePlanComponent> => {
      const { id, ...body } = payload;
      const { data } = await api.patch(`/api/v1/fee-plan-components/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-plan-components"] });
    },
  });
}

/**
 * Delete a fee plan component.
 */
export function useDeleteFeePlanComponent() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: number): Promise<void> => {
      await api.delete(`/api/v1/fee-plan-components/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-plan-components"] });
    },
  });
}

/* ------------------------------------------------------
   FEE ASSIGNMENTS
------------------------------------------------------- */
export function useFeeAssignments() {
  return useQuery({
    queryKey: ["fee-assignments"],
    queryFn: async (): Promise<FeeAssignment[]> => {
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
    }): Promise<FeeAssignment> => {
      const { data } = await api.post("/api/v1/fee-assignments", payload);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-assignments"] });
    },
  });
}

/**
 * Update an existing fee assignment.
 */
export function useUpdateFeeAssignment() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      id: number;
      invoice_id?: number | null;
      concession?: number;
      note?: string;
    }): Promise<FeeAssignment> => {
      const { id, ...body } = payload;
      const { data } = await api.patch(`/api/v1/fee-assignments/${id}`, body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-assignments"] });
    },
  });
}

/**
 * Delete a fee assignment.
 */
export function useDeleteFeeAssignment() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: async (id: number): Promise<void> => {
      await api.delete(`/api/v1/fee-assignments/${id}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fee-assignments"] });
    },
  });
}

/* ------------------------------------------------------
   LIST INVOICES (admin)
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
   LIST MY INVOICES (current user)
------------------------------------------------------- */
export function useMyInvoices() {
  return useQuery({
    queryKey: ["my-invoices"],
    queryFn: async (): Promise<Invoice[]> => {
      const { data } = await api.get("/api/v1/invoices/mine");
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
