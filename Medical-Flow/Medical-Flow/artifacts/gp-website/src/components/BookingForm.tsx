import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  ChevronRight,
  ChevronLeft,
  CheckCircle,
  Clock,
  Calendar as CalendarIcon,
  User,
  Stethoscope,
  CreditCard,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { useInView } from "@/hooks/useInView";

const APPOINTMENT_TYPES = [
  "General Consultation",
  "Online Consultation (Video call)",
  "Follow-up",
  "Chronic Care",
  "Sick Note / Certificate",
  "Other",
];

// Short clarifying notes shown under a service in the picker.
const TYPE_HINTS: Record<string, string> = {
  "General Consultation": "Walk-in at the practice — your time is a guide; you'll be seen in turn",
  "Online Consultation (Video call)": "Secure video call in your browser — we'll send you a private link",
};

const formSchema = z.object({
  name: z.string().min(2, "Name is required"),
  phone: z
    .string()
    .min(10, "Valid phone number is required")
    .regex(/^(\+27|0)[6-8][0-9]{8}$/, "Please enter a valid SA phone number"),
  email: z.string().email("A valid email is required for payment"),
  appointmentType: z.string().min(1, "Please select an appointment type"),
  date: z.string().min(1, "Please select a date"),
  time: z.string().min(1, "Please select an available time"),
});

type Slot = { time: string; available: boolean };

type FormValues = z.infer<typeof formSchema>;

const slideVariants = {
  enter: (dir: number) => ({ x: dir > 0 ? "100%" : "-100%", opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir: number) => ({ x: dir < 0 ? "100%" : "-100%", opacity: 0 }),
};

const STEPS = [
  { label: "Your Details", icon: User },
  { label: "Service", icon: Stethoscope },
  { label: "Date & Time", icon: CalendarIcon },
  { label: "Confirm", icon: CreditCard },
];

export default function BookingForm() {
  const { ref, isInView } = useInView({ threshold: 0.2 });
  const [step, setStep] = useState(1);
  const [direction, setDirection] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      phone: "",
      email: "",
      appointmentType: "",
      date: new Date().toISOString().split("T")[0],
      time: "",
    },
  });

  const watchedDate = form.watch("date");

  // Load bookable slots for the chosen date and merge in live availability
  // (Appointments + other website bookings) so taken times can't be picked.
  const loadSlots = async (date: string) => {
    if (!date) return;
    setSlotsLoading(true);
    try {
      const res = await fetch(`/api/availability?date=${encodeURIComponent(date)}`);
      const data = (await res.json()) as { slots?: Slot[] };
      const next = data.slots ?? [];
      setSlots(next);
      // Drop the selected time if it's no longer available.
      const chosen = form.getValues("time");
      if (chosen && !next.some((s) => s.time === chosen && s.available)) {
        form.setValue("time", "");
      }
    } catch {
      setSlots([]);
    } finally {
      setSlotsLoading(false);
    }
  };

  useEffect(() => {
    loadSlots(watchedDate);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [watchedDate]);

  // Allow other sections (e.g. the Online Consultation block) to pre-select a
  // service when they scroll the user to this form.
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ appointmentType?: string }>).detail;
      if (detail?.appointmentType) {
        form.setValue("appointmentType", detail.appointmentType, { shouldValidate: true });
      }
    };
    window.addEventListener("prefill-booking", handler);
    return () => window.removeEventListener("prefill-booking", handler);
  }, [form]);

  const nextStep = async () => {
    let isValid = false;
    if (step === 1) isValid = await form.trigger(["name", "phone", "email"]);
    else if (step === 2) isValid = await form.trigger(["appointmentType"]);
    else if (step === 3) isValid = await form.trigger(["date", "time"]);
    if (isValid) { setDirection(1); setStep(s => s + 1); }
  };

  const prevStep = () => { setDirection(-1); setStep(s => s - 1); };

  const submitBooking = async () => {
    const values = form.getValues();
    setIsProcessing(true);
    setApiError(null);

    try {
      // 1. Create booking
      const bookingRes = await fetch("/api/bookings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: values.name,
          phone: values.phone,
          email: values.email,
          appointmentType: values.appointmentType,
          date: values.date,
          time: values.time,
        }),
      });

      // The slot was taken between viewing and submitting — send them back to
      // pick another, with fresh availability.
      if (bookingRes.status === 409) {
        const err = await bookingRes.json().catch(() => ({}));
        setApiError((err as { error?: string }).error ?? "That time slot is no longer available.");
        await loadSlots(values.date);
        setDirection(-1);
        setStep(3);
        setIsProcessing(false);
        return;
      }

      if (!bookingRes.ok) {
        const err = await bookingRes.json().catch(() => ({}));
        throw new Error((err as { error?: string }).error ?? "Failed to create booking");
      }

      const { reference } = (await bookingRes.json()) as { reference: string };

      // Booking is just a request — confirm it and show the success screen.
      window.location.assign(`/?booking=requested&ref=${reference}`);
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setIsProcessing(false);
    }
  };

  const values = form.getValues();

  return (
    <section className="py-24 bg-white relative overflow-hidden" ref={ref}>
      <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 rounded-full bg-primary/5 blur-3xl" />
      <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-80 h-80 rounded-full bg-accent/5 blur-3xl" />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-100 text-orange-800 text-sm font-semibold mb-4">
            <Clock className="w-4 h-4" />
            Appointments filling fast today
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Book Your Appointment
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Reserve your spot in minutes. We'll confirm your appointment and any details with you directly.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
          transition={{ duration: 0.6 }}
          className="bg-white rounded-3xl shadow-xl border border-black/5 p-6 md:p-10 max-w-2xl mx-auto"
        >
          {/* Step progress */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-3">
              {STEPS.map((s, i) => {
                const Icon = s.icon;
                const num = i + 1;
                const active = step === num;
                const done = step > num;
                return (
                  <div key={s.label} className="flex flex-col items-center gap-1 flex-1">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${done ? "bg-primary text-white" : active ? "bg-primary/10 text-primary ring-2 ring-primary" : "bg-gray-100 text-gray-400"}`}>
                      {done ? <CheckCircle className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                    </div>
                    <span className={`text-[10px] font-semibold hidden sm:block ${active ? "text-primary" : done ? "text-primary/70" : "text-gray-400"}`}>
                      {s.label}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="w-full bg-gray-100 rounded-full h-1.5">
              <motion.div
                className="bg-primary h-1.5 rounded-full"
                initial={{ width: "25%" }}
                animate={{ width: `${(step / 4) * 100}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>

          <Form {...form}>
            <form className="relative min-h-[320px]">
              <AnimatePresence initial={false} custom={direction} mode="wait">

                {/* Step 1: Personal Details */}
                {step === 1 && (
                  <motion.div
                    key="step1"
                    custom={direction}
                    variants={slideVariants}
                    initial="enter"
                    animate="center"
                    exit="exit"
                    transition={{ type: "tween", duration: 0.28 }}
                    className="space-y-5"
                  >
                    <h3 className="text-xl font-bold flex items-center gap-2">
                      <User className="text-primary w-5 h-5" /> Your Details
                    </h3>
                    <FormField
                      control={form.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Full Name</FormLabel>
                          <FormControl>
                            <Input placeholder="Jane Dlamini" className="h-12 bg-gray-50/50" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="phone"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Phone Number</FormLabel>
                          <FormControl>
                            <Input placeholder="082 123 4567" type="tel" className="h-12 bg-gray-50/50" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email Address <span className="text-xs text-muted-foreground font-normal">(for payment confirmation)</span></FormLabel>
                          <FormControl>
                            <Input placeholder="jane@example.com" type="email" className="h-12 bg-gray-50/50" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>
                )}

                {/* Step 2: Appointment Type */}
                {step === 2 && (
                  <motion.div
                    key="step2"
                    custom={direction}
                    variants={slideVariants}
                    initial="enter"
                    animate="center"
                    exit="exit"
                    transition={{ type: "tween", duration: 0.28 }}
                    className="space-y-5"
                  >
                    <h3 className="text-xl font-bold flex items-center gap-2">
                      <Stethoscope className="text-primary w-5 h-5" /> What do you need help with?
                    </h3>
                    <FormField
                      control={form.control}
                      name="appointmentType"
                      render={({ field }) => (
                        <FormItem>
                          <FormControl>
                            <RadioGroup
                              onValueChange={field.onChange}
                              value={field.value}
                              className="grid grid-cols-1 gap-2"
                            >
                              {APPOINTMENT_TYPES.map((type) => {
                                return (
                                  <FormItem
                                    key={type}
                                    className="flex items-center space-x-3 space-y-0 p-3.5 border rounded-xl cursor-pointer hover:bg-gray-50 transition-colors [&:has([data-state=checked])]:border-primary [&:has([data-state=checked])]:bg-primary/5"
                                  >
                                    <FormControl>
                                      <RadioGroupItem value={type} />
                                    </FormControl>
                                    <div className="min-w-0">
                                      <FormLabel className="font-medium cursor-pointer block">{type}</FormLabel>
                                      {TYPE_HINTS[type] && (
                                        <span className="text-xs text-muted-foreground leading-snug block mt-0.5">{TYPE_HINTS[type]}</span>
                                      )}
                                    </div>
                                  </FormItem>
                                );
                              })}
                            </RadioGroup>
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>
                )}

                {/* Step 3: Date & Time */}
                {step === 3 && (
                  <motion.div
                    key="step3"
                    custom={direction}
                    variants={slideVariants}
                    initial="enter"
                    animate="center"
                    exit="exit"
                    transition={{ type: "tween", duration: 0.28 }}
                    className="space-y-6"
                  >
                    <h3 className="text-xl font-bold flex items-center gap-2">
                      <CalendarIcon className="text-primary w-5 h-5" /> When would you like to come in?
                    </h3>
                    <FormField
                      control={form.control}
                      name="date"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Preferred Date</FormLabel>
                          <FormControl>
                            <Input
                              type="date"
                              className="h-12 bg-gray-50/50"
                              min={new Date().toISOString().split("T")[0]}
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="time"
                      render={({ field }) => (
                        <FormItem className="space-y-3 pt-2">
                          <div className="flex items-center justify-between">
                            <FormLabel>Available Times</FormLabel>
                            {slotsLoading && (
                              <span className="text-xs text-muted-foreground flex items-center gap-1">
                                <Loader2 className="w-3 h-3 animate-spin" /> Checking availability…
                              </span>
                            )}
                          </div>
                          <FormControl>
                            {slots.length === 0 && !slotsLoading ? (
                              <div className="text-sm text-muted-foreground bg-gray-50 rounded-xl p-4 text-center">
                                No bookable times for this date. Please pick another day.
                              </div>
                            ) : (
                              <div className="grid grid-cols-3 sm:grid-cols-4 gap-2.5">
                                {slots.map((slot) => {
                                  const selected = field.value === slot.time;
                                  return (
                                    <button
                                      key={slot.time}
                                      type="button"
                                      disabled={!slot.available}
                                      onClick={() => field.onChange(slot.time)}
                                      className={[
                                        "py-2.5 rounded-xl text-sm font-semibold border transition-all duration-150",
                                        !slot.available
                                          ? "bg-gray-100 text-gray-300 border-gray-100 line-through cursor-not-allowed"
                                          : selected
                                          ? "bg-primary text-white border-primary shadow-sm"
                                          : "bg-white text-foreground border-gray-200 hover:border-primary hover:bg-primary/5",
                                      ].join(" ")}
                                      title={slot.available ? "" : "Already booked"}
                                      data-testid={`slot-${slot.time}`}
                                    >
                                      {slot.time}
                                    </button>
                                  );
                                })}
                              </div>
                            )}
                          </FormControl>
                          <p className="text-xs text-muted-foreground">Greyed-out times are already booked.</p>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </motion.div>
                )}

                {/* Step 4: Review & Pay */}
                {step === 4 && (
                  <motion.div
                    key="step4"
                    custom={direction}
                    variants={slideVariants}
                    initial="enter"
                    animate="center"
                    exit="exit"
                    transition={{ type: "tween", duration: 0.28 }}
                    className="space-y-5"
                  >
                    <h3 className="text-xl font-bold flex items-center gap-2">
                      <CreditCard className="text-primary w-5 h-5" /> Review &amp; Confirm
                    </h3>

                    {/* Summary */}
                    <div className="bg-gray-50 rounded-2xl p-5 space-y-3 text-sm">
                      {[
                        ["Name", values.name],
                        ["Phone", values.phone],
                        ["Email", values.email],
                        ["Service", values.appointmentType],
                        ["Date", values.date],
                        ["Time", values.time],
                      ].map(([label, val]) => (
                        <div key={label} className="flex justify-between">
                          <span className="text-muted-foreground">{label}</span>
                          <span className="font-medium text-right max-w-[60%]">{val}</span>
                        </div>
                      ))}
                    </div>

                    {/* What happens next */}
                    <div className="rounded-xl bg-primary/5 border border-primary/10 p-4 text-sm text-foreground/80 flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                      <span>No payment is needed to book. We'll contact you to confirm your appointment and any details.</span>
                    </div>

                    {/* Error */}
                    {apiError && (
                      <div className="rounded-xl bg-red-50 border border-red-100 p-4 text-sm text-red-700 flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                        {apiError}
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Navigation */}
              <div className="flex justify-between items-center mt-8 pt-6 border-t">
                {step > 1 ? (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={prevStep}
                    disabled={isProcessing}
                    className="gap-2"
                  >
                    <ChevronLeft className="w-4 h-4" /> Back
                  </Button>
                ) : (
                  <div />
                )}

                {step < 4 ? (
                  <Button
                    type="button"
                    onClick={nextStep}
                    className="gap-2 rounded-full px-6"
                  >
                    Continue <ChevronRight className="w-4 h-4" />
                  </Button>
                ) : (
                  <Button
                    type="button"
                    onClick={submitBooking}
                    disabled={isProcessing}
                    className="gap-2 rounded-full px-8 shadow-lg"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Submitting…
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4" />
                        Confirm booking
                      </>
                    )}
                  </Button>
                )}
              </div>
            </form>
          </Form>
        </motion.div>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Booking takes under a minute. We'll be in touch to confirm your appointment.
        </p>
      </div>
    </section>
  );
}
