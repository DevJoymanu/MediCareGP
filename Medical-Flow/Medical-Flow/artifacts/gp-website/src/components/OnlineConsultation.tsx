import { motion } from "framer-motion";
import { useInView } from "@/hooks/useInView";
import {
  Video,
  MessageSquare,
  MonitorSmartphone,
  ShieldCheck,
  Calendar,
  CheckCircle,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const CONSULT_FEE = "R350"; // online consultation fee
// Must match APPOINTMENT_TYPES in BookingForm.tsx and ONLINE_CONSULT_TYPE in Django settings.
const ONLINE_TYPE = "Online Consultation (Video call)";

// Jump to the booking form and pre-select the online consultation type.
function bookOnline() {
  window.dispatchEvent(
    new CustomEvent("prefill-booking", { detail: { appointmentType: ONLINE_TYPE } }),
  );
  document.getElementById("booking")?.scrollIntoView({ behavior: "smooth" });
}

const steps = [
  {
    icon: Calendar,
    step: "1",
    title: "Book online",
    description:
      'Choose "Online Consultation" in the booking form above and pick a date and time that suits you. It takes under a minute.',
    color: "bg-blue-50 text-blue-600",
    ring: "ring-blue-100",
  },
  {
    icon: MessageSquare,
    step: "2",
    title: "We confirm your slot",
    description:
      "We'll contact you to confirm your appointment, then send you a private, secure video link by WhatsApp or email.",
    color: "bg-teal-50 text-teal-600",
    ring: "ring-teal-100",
  },
  {
    icon: MonitorSmartphone,
    step: "3",
    title: "Open your link",
    description:
      "Tap your private link at your appointment time — no app, no account, no codes. Works on your phone, tablet, or PC.",
    color: "bg-violet-50 text-violet-600",
    ring: "ring-violet-100",
  },
  {
    icon: Video,
    step: "4",
    title: "Consult with the doctor",
    description:
      "You connect to the doctor directly for a full, private video consultation — from wherever you are.",
    color: "bg-green-50 text-green-600",
    ring: "ring-green-100",
  },
];

const included = [
  "Full video consultation with the doctor",
  "Diagnosis and treatment advice",
  "Prescription sent via WhatsApp (where applicable)",
  "Referral letter if needed",
  "Follow-up WhatsApp message included",
];

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const cardVariant = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 220, damping: 22 } },
};

export default function OnlineConsultation() {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  return (
    <section
      id="online-consultation"
      ref={ref}
      className="py-24 relative overflow-hidden"
    >
      {/* Gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/8 via-background to-accent/8 -z-10" />
      <div className="absolute top-0 right-0 w-[40%] h-[40%] rounded-full bg-primary/5 blur-[120px] -z-10" />
      <div className="absolute bottom-0 left-0 w-[35%] h-[35%] rounded-full bg-accent/8 blur-[120px] -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-semibold mb-4"
          >
            <Video className="w-4 h-4" />
            Online Consultations — Secure video in your browser
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.08 }}
            className="text-3xl md:text-4xl font-bold text-foreground mb-4"
          >
            See the doctor from anywhere
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, delay: 0.14 }}
            className="text-lg text-muted-foreground leading-relaxed"
          >
            Can't make it in person? Book a secure video consultation from your phone, tablet, or PC. No app download, no account — just click and connect.
          </motion.p>
        </div>

        {/* How it works steps */}
        <motion.div
          variants={container}
          initial="hidden"
          animate={isInView ? "show" : "hidden"}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16"
        >
          {steps.map((s, i) => {
            const Icon = s.icon;
            return (
              <motion.div
                key={i}
                variants={cardVariant}
                className="relative flex flex-col items-center text-center p-6 rounded-2xl bg-white border border-black/5 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
                data-testid={`card-online-step-${i}`}
              >
                {/* Step number */}
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center shadow">
                  {s.step}
                </span>
                {/* Connector line (not last) */}
                {i < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-10 left-full w-full h-px border-t-2 border-dashed border-primary/20 -z-10 translate-x-[-50%]" />
                )}
                <div className={`w-14 h-14 rounded-2xl ${s.color} ring-4 ${s.ring} flex items-center justify-center mb-4`}>
                  <Icon className="w-7 h-7" />
                </div>
                <h3 className="font-bold text-foreground mb-2">{s.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{s.description}</p>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Bottom two-column: pricing + join room */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Pricing & payment details */}
          <motion.div
            initial={{ opacity: 0, x: -24 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="rounded-3xl bg-white border border-black/5 shadow-sm p-8 space-y-6"
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-2xl font-bold text-foreground">Online Consultation</h3>
                <p className="text-muted-foreground text-sm mt-1">Secure video call in your browser · Private</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-primary">{CONSULT_FEE}</div>
                <div className="text-xs text-muted-foreground">per consultation</div>
              </div>
            </div>

            {/* What's included */}
            <ul className="space-y-2.5">
              {included.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm text-foreground/80">
                  <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                  {item}
                </li>
              ))}
            </ul>

            {/* How booking works */}
            <div className="rounded-2xl bg-gray-50 border border-black/5 p-5 space-y-2">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-primary" />
                <span className="text-sm font-bold text-foreground">Book online in a minute</span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Request your online consultation right here on the website — no WhatsApp back-and-forth. We'll confirm your appointment with you.
              </p>
            </div>

            <div className="flex items-start gap-2 text-xs text-muted-foreground bg-amber-50 border border-amber-100 rounded-xl p-3">
              <Info className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
              Once you've booked, we'll confirm your slot and send you a private, secure video link by WhatsApp or email.
            </div>

            <Button
              onClick={bookOnline}
              className="w-full rounded-xl py-6 text-base shadow-md hover:shadow-lg transition-all duration-200"
              data-testid="btn-book-online-consultation"
            >
              <Video className="w-5 h-5 mr-2" />
              Book Online Consultation
            </Button>
          </motion.div>

          {/* Join waiting room */}
          <motion.div
            initial={{ opacity: 0, x: 24 }}
            animate={isInView ? { opacity: 1, x: 0 } : {}}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col gap-6"
          >
            {/* Already booked card */}
            <div className="rounded-3xl bg-primary text-white p-8 shadow-lg flex flex-col gap-5 flex-1">
              <div className="w-14 h-14 rounded-2xl bg-white/15 flex items-center justify-center">
                <Video className="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold mb-2">Already booked?</h3>
                <p className="text-white/80 text-sm leading-relaxed">
                  When it's time, just open the private video link we sent you by WhatsApp or email. It runs right in your browser — no app, no account, no codes. The doctor joins you directly.
                </p>
              </div>
              <div className="mt-auto flex items-center gap-2 text-white/90 text-sm font-medium bg-white/10 rounded-xl px-4 py-3">
                <ShieldCheck className="w-5 h-5 flex-shrink-0" />
                Private and encrypted — your call is peer-to-peer.
              </div>
            </div>

            {/* Tips card */}
            <div className="rounded-3xl bg-white border border-black/5 shadow-sm p-6 space-y-3">
              <h4 className="font-bold text-foreground flex items-center gap-2">
                <MonitorSmartphone className="w-4 h-4 text-primary" />
                Before your consultation
              </h4>
              <ul className="space-y-2">
                {[
                  "Use Chrome or Firefox for best video quality",
                  "Find a quiet, private space with good lighting",
                  "Have your ID and medical aid card nearby",
                  "Test your camera and microphone beforehand",
                  "Have a list of your current medications ready",
                ].map((tip) => (
                  <li key={tip} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <CheckCircle className="w-4 h-4 text-primary/60 flex-shrink-0 mt-0.5" />
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        </div>

        {/* Bottom CTA strip */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="mt-10 text-center"
        >
          <p className="text-sm text-muted-foreground">
            Prefer an in-person visit?{" "}
            <button
              onClick={() => document.getElementById("booking")?.scrollIntoView({ behavior: "smooth" })}
              className="text-primary font-semibold hover:underline underline-offset-2"
              data-testid="btn-switch-to-inperson"
            >
              Book an in-person appointment
            </button>{" "}
            instead.
          </p>
        </motion.div>
      </div>
    </section>
  );
}
