import { Router, type Request } from "express";
import { db } from "@workspace/db";
import { bookingsTable } from "@workspace/db";
import { eq } from "drizzle-orm";
import crypto from "crypto";
import { z } from "zod";

const router = Router();

const PAYFAST_SANDBOX_URL = "https://sandbox.payfast.co.za/eng/process";
const PAYFAST_LIVE_URL = "https://www.payfast.co.za/eng/process";

const SANDBOX_MERCHANT_ID = "10000100";
const SANDBOX_MERCHANT_KEY = "46f0cd694581a";

function isProduction(): boolean {
  return process.env.NODE_ENV === "production";
}

function getMerchantId(): string {
  return process.env.PAYFAST_MERCHANT_ID ?? SANDBOX_MERCHANT_ID;
}

function getMerchantKey(): string {
  return process.env.PAYFAST_MERCHANT_KEY ?? SANDBOX_MERCHANT_KEY;
}

function getPayfastUrl(): string {
  return isProduction() && process.env.PAYFAST_MERCHANT_ID
    ? PAYFAST_LIVE_URL
    : PAYFAST_SANDBOX_URL;
}

function getBaseUrl(_req: Request): string {
  const domains = process.env.REPLIT_DOMAINS;
  if (domains) {
    const first = domains.split(",")[0].trim();
    return `https://${first}`;
  }
  const dev = process.env.REPLIT_DEV_DOMAIN;
  if (dev) return `https://${dev}`;
  return "http://localhost:80";
}

function buildSignature(
  params: Record<string, string>,
  passphrase?: string,
): string {
  const parts = Object.entries(params)
    .filter(([, v]) => v !== "" && v !== undefined && v !== null)
    .map(
      ([k, v]) =>
        `${k}=${encodeURIComponent(v.toString()).replace(/%20/g, "+")}`,
    );

  let pfString = parts.join("&");
  if (passphrase) {
    pfString += `&passphrase=${encodeURIComponent(passphrase).replace(/%20/g, "+")}`;
  }

  return crypto.createHash("md5").update(pfString).digest("hex");
}

const initiateSchema = z.object({
  reference: z.string().min(1),
});

router.post("/payments/payfast/initiate", async (req, res) => {
  const parsed = initiateSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid request" });
    return;
  }

  const { reference } = parsed.data;

  try {
    const [booking] = await db
      .select()
      .from(bookingsTable)
      .where(eq(bookingsTable.reference, reference))
      .limit(1);

    if (!booking) {
      res.status(404).json({ error: "Booking not found" });
      return;
    }

    const baseUrl = getBaseUrl(req);
    const amountRand = (booking.amountCents / 100).toFixed(2);
    const nameParts = booking.name.trim().split(" ");
    const firstName = nameParts[0] ?? booking.name;
    const lastName = nameParts.slice(1).join(" ") || "-";

    const params: Record<string, string> = {
      merchant_id: getMerchantId(),
      merchant_key: getMerchantKey(),
      return_url: `${baseUrl}/?booking=success&ref=${reference}`,
      cancel_url: `${baseUrl}/?booking=cancelled`,
      notify_url: `${baseUrl}/api/payments/payfast/notify`,
      name_first: firstName,
      name_last: lastName,
      email_address: booking.email ?? "",
      cell_number: booking.phone.replace(/\D/g, "").replace(/^0/, "27"),
      m_payment_id: reference,
      amount: amountRand,
      item_name: `Rand Medical Resources - ${booking.appointmentType}`,
      item_description: `Appointment on ${booking.appointmentDate} (${booking.timeSlot})`,
    };

    if (!params.cell_number) delete params.cell_number;
    if (!params.email_address) delete params.email_address;

    const passphrase = process.env.PAYFAST_PASSPHRASE;
    const signature = buildSignature(params, passphrase);
    params.signature = signature;

    res.json({
      paymentUrl: getPayfastUrl(),
      fields: params,
    });
  } catch (err) {
    req.log.error(err, "Failed to initiate PayFast payment");
    res.status(500).json({ error: "Failed to initiate payment" });
  }
});

router.post("/payments/payfast/notify", async (req, res) => {
  try {
    const body = req.body as Record<string, string>;
    const pfPaymentId = body.pf_payment_id;
    const mPaymentId = body.m_payment_id;
    const paymentStatus = body.payment_status;

    req.log.info({ mPaymentId, pfPaymentId, paymentStatus }, "PayFast ITN received");

    if (paymentStatus === "COMPLETE" && mPaymentId) {
      await db
        .update(bookingsTable)
        .set({ status: "paid", payfastPaymentId: pfPaymentId })
        .where(eq(bookingsTable.reference, mPaymentId));
    }

    res.status(200).send("OK");
  } catch (err) {
    req.log.error(err, "Failed to process PayFast ITN");
    res.status(200).send("OK");
  }
});

export default router;
