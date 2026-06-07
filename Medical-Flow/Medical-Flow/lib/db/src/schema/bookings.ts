import { pgTable, serial, text, integer, timestamp } from "drizzle-orm/pg-core";
import { z } from "zod";

export const bookingsTable = pgTable("bookings", {
  id: serial("id").primaryKey(),
  reference: text("reference").notNull().unique(),
  name: text("name").notNull(),
  phone: text("phone").notNull(),
  email: text("email"),
  appointmentType: text("appointment_type").notNull(),
  appointmentDate: text("appointment_date").notNull(),
  timeSlot: text("time_slot").notNull(),
  amountCents: integer("amount_cents").notNull(),
  status: text("status").notNull().default("pending_payment"),
  payfastPaymentId: text("payfast_payment_id"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const insertBookingSchema = z.object({
  reference: z.string(),
  name: z.string(),
  phone: z.string(),
  email: z.string().nullable().optional(),
  appointmentType: z.string(),
  appointmentDate: z.string(),
  timeSlot: z.string(),
  amountCents: z.number().int(),
  status: z.string().optional(),
  payfastPaymentId: z.string().nullable().optional(),
});

export type InsertBooking = z.infer<typeof insertBookingSchema>;
export type Booking = typeof bookingsTable.$inferSelect;
