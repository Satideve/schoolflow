/**
 * C:\coding_projects\dev\schoolflow\frontend\src\api\payments.ts
 * Payment API wrapper — converts rupees to paise for orders, and for manual provider
 * simulates a webhook using rupees (so the backend records paid_amount correctly).
 *
 * Developer note: this simulated webhook is a dev convenience. Remove or replace
 * with proper provider flow in production.
 */

import client from "./client";

export type CreatePaymentPayload = {
  amount: number; // rupees (e.g. 100.50)
  provider: string; // "manual" | "fake" | "razorpay"
  note?: string;
};

type OrderResponse = {
  order?: any;
  webhook?: any;
};

function makeId(prefix = "manual") {
  return `${prefix}-${Date.now().toString(36)}-${Math.random()
    .toString(36)
    .slice(2, 8)}`;
}

export async function createPaymentOrder(
  invoiceId: string | number,
  payload: CreatePaymentPayload
): Promise<OrderResponse> {
  // Convert rupees to paise for the order
  const amountInPaise = Math.round(Number(payload.amount) * 100);

  const body = {
    amount: amountInPaise,
    provider: payload.provider,
    ...(payload.note ? { note: payload.note } : {}),
  };

  // Debug: log what we are about to call
  console.debug(
    "[payments] createPaymentOrder → POST /api/v1/payments/create-order/",
    invoiceId,
    "body:",
    body
  );

  // 1) create order (amount in paise)
  const orderResp = await client.post(
    `/api/v1/payments/create-order/${invoiceId}`,
    body
  );
  const orderData = orderResp.data;

  // If provider is manual, try to immediately simulate a webhook to mark as captured.
  if (payload.provider === "manual") {
    try {
      const providerTxnId = makeId("manual");
      // IMPORTANT: send amount in RUPEES for the webhook so backend records the correct units
      const amountInRupeesForWebhook = Number(payload.amount);

      const webhookBody = {
        provider: "manual",
        invoice_id: invoiceId,
        provider_txn_id: providerTxnId,
        order_id: orderData?.order?.id ?? null,
        amount: amountInRupeesForWebhook,
        status: "captured",
        note: payload.note ?? null,
      };

      console.debug(
        "[payments] simulate manual webhook → POST /api/v1/payments/webhook body:",
        webhookBody
      );

      const webhookResp = await client.post(
        `/api/v1/payments/webhook`,
        webhookBody
      );
      return { order: orderData, webhook: webhookResp.data };
    } catch (err: any) {
      console.error(
        "Manual webhook simulation failed:",
        err?.response?.data ?? err?.message ?? err
      );
      return { order: orderData, webhook: null };
    }
  }

  // For non-manual providers, just return the order info.
  return { order: orderData };
}
