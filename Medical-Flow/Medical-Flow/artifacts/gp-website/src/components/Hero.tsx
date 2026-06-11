import { motion } from "framer-motion";
import { SiWhatsapp } from "react-icons/si";
import { Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import doctorImg from "@assets/doctor2.jpg";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.18 }
  }
};

const item = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 260, damping: 22 } }
};

const photoVariant = {
  hidden: { opacity: 0, scale: 0.92, x: 40 },
  show: { opacity: 1, scale: 1, x: 0, transition: { type: "spring" as const, stiffness: 200, damping: 26, delay: 0.3 } }
};

export default function Hero() {
  const scrollToBooking = () => {
    document.getElementById("booking")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="relative min-h-[90vh] flex items-center overflow-hidden pt-16 pb-16 px-4 sm:px-6 lg:px-8">
      {/* Background medical image — slow Ken Burns zoom */}
      <div className="absolute inset-0 z-0 overflow-hidden">
        <motion.img
          src="https://images.unsplash.com/photo-1504813184591-01572f98c85f?auto=format&fit=crop&w=1920&q=80"
          alt=""
          aria-hidden="true"
          className="w-full h-full object-cover object-center"
          initial={{ scale: 1 }}
          animate={{ scale: 1.08 }}
          transition={{ duration: 22, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
        />
        {/* Layered gradient overlay — keeps image subtle and text readable */}
        <div className="absolute inset-0 bg-gradient-to-r from-white/92 via-white/82 to-white/55" />
        <div className="absolute inset-0 bg-gradient-to-b from-white/30 via-transparent to-white/40" />
        {/* Tint to match the site's blue palette */}
        <div className="absolute inset-0 bg-primary/8" />
      </div>

      {/* Ambient blobs — on top of image */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-[1]">
        <motion.div
          animate={{ y: [0, -24, 0], opacity: [0.18, 0.32, 0.18], scale: [1, 1.06, 1] }}
          transition={{ duration: 9, repeat: Infinity, ease: "easeInOut" }}
          className="absolute -top-[15%] -right-[8%] w-[55%] h-[55%] rounded-full bg-primary/10 blur-[120px]"
        />
        <motion.div
          animate={{ y: [0, 22, 0], opacity: [0.10, 0.22, 0.10], scale: [1, 1.12, 1] }}
          transition={{ duration: 11, repeat: Infinity, ease: "easeInOut", delay: 1.5 }}
          className="absolute top-[45%] -left-[10%] w-[45%] h-[45%] rounded-full bg-accent/10 blur-[120px]"
        />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">

          {/* Left — text content */}
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="flex flex-col space-y-7 text-center lg:text-left items-center lg:items-start"
          >
            {/* Status pill */}
            <motion.div
              variants={item}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/70 backdrop-blur-sm border border-black/5 shadow-sm"
            >
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-sm font-medium text-foreground/80">Open Now · Accepting Walk-ins</span>
            </motion.div>

            <motion.h1
              variants={item}
              className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-foreground leading-[1.1]"
            >
              Healthcare that<br />
              feels like <span className="text-primary">home.</span>
            </motion.h1>

            <motion.p variants={item} className="text-lg md:text-xl text-muted-foreground max-w-xl leading-relaxed">
              Trusted General Practitioner in Kwa-Thema, Springs. Comprehensive medical care for you and your family, without the rush.
            </motion.p>

            {/* CTAs */}
            <motion.div variants={item} className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
              <Button
                size="lg"
                className="text-base px-8 py-6 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 animate-glow relative overflow-hidden group"
                onClick={scrollToBooking}
                data-testid="hero-book-btn"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite]" />
                <Calendar className="mr-2 h-5 w-5" />
                Book Appointment
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="text-base px-8 py-6 rounded-full bg-white/50 backdrop-blur-sm border-2 border-primary/20 hover:bg-primary/5 hover:border-primary/40 transition-all duration-300 transform hover:-translate-y-1 text-primary"
                onClick={() => window.open("https://wa.me/27726033299", "_blank")}
                data-testid="hero-whatsapp-btn"
              >
                <SiWhatsapp className="mr-2 h-5 w-5 text-green-500" />
                WhatsApp Us
              </Button>
            </motion.div>

            {/* Trust chips */}
            <motion.div variants={item} className="flex flex-wrap justify-center lg:justify-start gap-5 text-sm text-muted-foreground font-medium pt-2">
              {["HPCSA Registered", "Same-Day Appointments", "Medical Aid Accepted"].map((badge) => (
                <div key={badge} className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
                    <svg className="w-3 h-3 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  {badge}
                </div>
              ))}
            </motion.div>
          </motion.div>

          {/* Right — doctor portrait */}
          <motion.div
            variants={photoVariant}
            initial="hidden"
            animate="show"
            className="flex justify-center lg:justify-end"
          >
            <div className="relative">
              {/* Outer decorative ring — slow rotation */}
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
                className="absolute -inset-4 rounded-full border-2 border-dashed border-primary/20"
              />

              {/* Soft glow halo */}
              <motion.div
                animate={{ scale: [1, 1.06, 1], opacity: [0.4, 0.7, 0.4] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="absolute inset-0 rounded-full bg-primary/10 blur-2xl"
              />

              {/* Photo frame */}
              <div className="relative w-64 h-64 sm:w-80 sm:h-80 rounded-full overflow-hidden border-4 border-white shadow-2xl ring-1 ring-primary/10">
                <img
                  src={doctorImg}
                  alt="Your General Practitioner"
                  className="w-full h-full object-cover object-center"
                  data-testid="img-doctor-portrait"
                />
              </div>

              {/* Floating experience badge */}
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.9, type: "spring" as const, stiffness: 260, damping: 20 }}
                className="absolute -bottom-4 -left-4 bg-white rounded-2xl px-4 py-3 shadow-xl border border-black/5 backdrop-blur-sm"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                    <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-medium">HPCSA Registered</p>
                    <p className="text-sm font-bold text-foreground">25+ Years Experience</p>
                  </div>
                </div>
              </motion.div>

              {/* Floating available badge */}
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 1.1, type: "spring" as const, stiffness: 260, damping: 20 }}
                className="absolute -top-2 -right-4 bg-white rounded-2xl px-4 py-3 shadow-xl border border-black/5 backdrop-blur-sm"
              >
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse flex-shrink-0" />
                  <p className="text-sm font-semibold text-foreground whitespace-nowrap">Appointments Available</p>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
