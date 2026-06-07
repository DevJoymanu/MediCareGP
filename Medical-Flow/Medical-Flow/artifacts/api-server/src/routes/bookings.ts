import { Router } from "express";
import { db } from "@workspace/db";
import { bookingsTable } from "@workspace/db";
import { eq } from "drizzle-orm";
import { z } from "zod";
import crypto from "crypto";

const router = Router();

const CONSULTATION_FEES: Record<string, number> = {
  "General Consultation": 350,
  "Online Consultation (Doxy.me)": 350,
  "Follow-up": 250,
  "Chronic Care": 350,
  "Sick Note / Certificate": 150,
  "Other": 350,
};

const createBookingSchema = z.object({
  name: z.string().min(2),
  phone: z.string().min(10),
  email: z.string().email(),
  appointmentType: z.string().min(1),
  date: z.string().min(1),
  timeSlot: z.string().min(1),
});

router.post("/bookings", async (req, res) => {
  const parsed = createBookingSchema.safeParse(req.body);
  if (!parsed.success) {
    res.status(400).json({ error: "Invalid booking data", details: parsed.error.issues });
    return;
  }

  const body = parsed.data;
  const fee = CONSULTATION_FEES[body.appointmentType] ?? 350;
  const amountCents = fee * 100;

  const timestamp = Date.now().toString(36).toUpperCase();
  const random = crypto.randomBytes(3).toString("hex").toUpperCase();
  const reference = `RMR-${timestamp}-${random}`;

  try {
    const [booking] = await db
      .insert(bookingsTable)
      .values({
        reference,
        name: body.name,
        phone: body.phone,
        email: body.email,
        appointmentType: body.appointmentType,
        appointmentDate: body.date,
        timeSlot: body.timeSlot,
        amountCents,
        status: "pending_payment",
      })
      .returning();

    res.status(201).json({
      reference: booking.reference,
      fee,
      amountCents: booking.amountCents,
    });
  } catch (err) {
    req.log.error(err, "Failed to create booking");
    res.status(500).json({ error: "Failed to create booking" });
  }
});

router.get("/bookings/:reference", async (req, res) => {
  const { reference } = req.params;

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

    res.json({
      reference: booking.reference,
      name: booking.name,
      appointmentType: booking.appointmentType,
      appointmentDate: booking.appointmentDate,
      timeSlot: booking.timeSlot,
      status: booking.status,
      fee: booking.amountCents / 100,
    });
  } catch (err) {
    req.log.error(err, "Failed to get booking");
    res.status(500).json({ error: "Failed to get booking" });
  }
});

export default router;
