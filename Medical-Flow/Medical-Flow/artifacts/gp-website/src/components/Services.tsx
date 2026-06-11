import { motion } from "framer-motion";
import { useInView } from "@/hooks/useInView";
import { Stethoscope, HeartPulse, ShieldCheck, Syringe, Briefcase, Calendar, ArrowRight, Video } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";

const WHATSAPP_BASE = "https://wa.me/27726033299?text=";

// `bookingType` pre-selects the matching option in the booking form when the
// patient clicks "Book This Service". `waText` is only ever a general enquiry —
// booking & payment always happen on the website, never over WhatsApp.
const services = [
  {
    icon: Stethoscope,
    title: "General Consultations",
    description: "Comprehensive medical assessments for acute illnesses, infections, and general health concerns.",
    bookingType: "General Consultation",
    waText: "Hi, I have a question about General Consultations."
  },
  {
    icon: Video,
    title: "Online Consultations",
    description: "See the doctor from home via a secure video call in your browser. No app needed — we send you a private link to click and connect.",
    bookingType: "Online Consultation (Video call)",
    waText: "Hi, I have a question about Online Consultations.",
    highlight: true
  },
  {
    icon: HeartPulse,
    title: "Chronic Disease Management",
    description: "Ongoing care and monitoring for diabetes, hypertension, asthma, and other chronic conditions.",
    bookingType: "Chronic Care",
    waText: "Hi, I have a question about Chronic Disease Management."
  },
  {
    icon: ShieldCheck,
    title: "Preventive Care",
    description: "Health screenings, wellness checks, vaccinations, and lifestyle counseling to keep you healthy.",
    bookingType: "General Consultation",
    waText: "Hi, I have a question about Preventive Care / Wellness checks."
  },
  {
    icon: Syringe,
    title: "Minor Procedures",
    description: "Wound suturing, removal of minor skin lesions, abscess drainage, and dressing changes.",
    bookingType: "Other",
    waText: "Hi, I have a question about Minor Procedures."
  },
  {
    icon: Briefcase,
    title: "Occupational Health",
    description: "Pre-employment medicals, fitness certificates, and work-related health evaluations.",
    bookingType: "Other",
    waText: "Hi, I have a question about Occupational Health assessments."
  }
];

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 200, damping: 20 } }
};

export default function Services() {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  const scrollToBooking = (appointmentType?: string) => {
    if (appointmentType) {
      window.dispatchEvent(
        new CustomEvent("prefill-booking", { detail: { appointmentType } }),
      );
    }
    document.getElementById("booking")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="py-24 bg-gray-50/50" id="services" ref={ref}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Comprehensive Care for the Whole Family
          </h2>
          <p className="text-lg text-muted-foreground">
            We provide a wide range of medical services tailored to your needs, ensuring you receive the highest standard of care in a comfortable environment.
          </p>
        </div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? "show" : "hidden"}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {services.map((service, index) => {
            const Icon = service.icon;
            return (
              <motion.div
                key={index}
                variants={itemVariants}
                className="group flex flex-col p-8 rounded-2xl bg-white shadow-sm hover:shadow-xl border border-black/5 transition-all duration-300 hover:-translate-y-1"
                data-testid={`card-service-${index}`}
              >
                {/* Icon */}
                <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 group-hover:bg-primary/20">
                  <Icon className="h-7 w-7 text-primary group-hover:animate-pulse" />
                </div>

                {/* Content */}
                <h3 className="text-xl font-bold text-foreground mb-3">{service.title}</h3>
                <p className="text-muted-foreground leading-relaxed flex-1 mb-6">
                  {service.description}
                </p>

                {/* CTAs */}
                <div className="flex flex-col sm:flex-row gap-2 mt-auto pt-4 border-t border-black/5">
                  {/* Book this service */}
                  <button
                    onClick={() => scrollToBooking(service.bookingType)}
                    className="relative flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-white text-sm font-semibold overflow-hidden
                      hover:bg-primary/90 active:scale-95 transition-all duration-200 shadow-sm hover:shadow-md group/btn"
                    data-testid={`btn-book-service-${index}`}
                  >
                    {/* Ripple shimmer */}
                    <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover/btn:translate-x-full transition-transform duration-700" />
                    <Calendar className="w-4 h-4 flex-shrink-0" />
                    Book This Service
                  </button>

                  {/* WhatsApp shortcut */}
                  <a
                    href={`${WHATSAPP_BASE}${encodeURIComponent(service.waText)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl border border-green-200 bg-green-50 text-green-700 text-sm font-semibold
                      hover:bg-green-100 hover:border-green-300 active:scale-95 transition-all duration-200 group/wa"
                    data-testid={`link-whatsapp-service-${index}`}
                  >
                    <SiWhatsapp className="w-4 h-4 flex-shrink-0 text-green-600" />
                    <span className="hidden sm:inline">WhatsApp</span>
                    <ArrowRight className="w-3.5 h-3.5 flex-shrink-0 opacity-60 group-hover/wa:translate-x-0.5 transition-transform duration-200" />
                  </a>
                </div>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Section-level CTA */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="text-center mt-14"
        >
          <p className="text-muted-foreground mb-5">Not sure which service you need?</p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => scrollToBooking("General Consultation")}
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:scale-95 transition-all duration-200"
              data-testid="btn-book-general"
            >
              <Calendar className="w-5 h-5" />
              Book a General Consultation
            </button>
            <a
              href="https://wa.me/27726033299?text=Hi%2C+I%27m+not+sure+which+service+I+need+and+would+like+some+advice."
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-full border-2 border-green-500 text-green-700 font-semibold hover:bg-green-50 hover:-translate-y-0.5 active:scale-95 transition-all duration-200"
              data-testid="link-whatsapp-advice"
            >
              <SiWhatsapp className="w-5 h-5 text-green-600" />
              Ask us on WhatsApp
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
