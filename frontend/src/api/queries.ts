/* C:\coding_projects\dev\schoolflow\frontend\src\api\queries.ts */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import type {
  InvoiceCreateDTO,
  Invoice,
  Receipt,
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
