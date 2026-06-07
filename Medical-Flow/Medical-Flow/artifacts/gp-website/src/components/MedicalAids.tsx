import { motion } from "framer-motion";
import { useInView } from "@/hooks/useInView";
import { ShieldCheck } from "lucide-react";

const medicalAids = [
  "Bankmed",
  "BestMed",
  "Bonitas",
  "Discovery",
  "Fedhealth",
  "Old Mutual",
  "Liberty",
  "Opmed",
  "Medihelp",
  "Momentum Health",
  "Medical Aid Society",
  "Sasol Medical Aid",
  "Xstrata Alloys Medical Aid",
  "Spectramed",
  "Post Office MediPos",
  "LAHealth",
  "GEMS",
  "Resolution Health",
  "Afrox Medical Aid Society",
  "KeyHealth",
  "Hosmed",
  "TopMed",
  "Umvuzo Health",
  "Transmed",
  "Sizwe Medical Fund",
  "SAB Medical Aid",
  "Remedi",
  "SelfMed",
  "FGILMED",
  "Netcare",
  "Profmed",
  "Nedgroup Medical Aid Scheme",
  "Medshield",
  "Moto Health Care",
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.04, delayChildren: 0.1 },
  },
};

const chip = {
  hidden: { opacity: 0, scale: 0.85, y: 10 },
  show: { opacity: 1, scale: 1, y: 0, transition: { type: "spring" as const, stiffness: 260, damping: 20 } },
};

export default function MedicalAids() {
  const { ref, isInView } = useInView({ threshold: 0.1 });

  return (
    <section
      id="medical-aids"
      ref={ref}
      className="py-24 bg-gradient-to-b from-white to-primary/5"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-semibold mb-4">
            <ShieldCheck className="w-4 h-4" />
            Accepted Medical Aids
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            We accept most major medical aids
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Our practice is registered with a wide range of medical aid schemes. If yours is not listed, please contact us — we will do our best to assist.
          </p>
        </div>

        {/* Aid chips */}
        <motion.div
          variants={container}
          initial="hidden"
          animate={isInView ? "show" : "hidden"}
          className="flex flex-wrap justify-center gap-3"
          data-testid="medical-aids-grid"
        >
          {medicalAids.map((aid) => (
            <motion.div
              key={aid}
              variants={chip}
              className="group flex items-center gap-2 px-4 py-2.5 rounded-full bg-white border border-primary/10 shadow-sm hover:shadow-md hover:border-primary/30 hover:-translate-y-0.5 transition-all duration-200 cursor-default"
              data-testid={`badge-medical-aid-${aid.toLowerCase().replace(/\s+/g, "-")}`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-primary/50 group-hover:bg-primary transition-colors duration-200 flex-shrink-0" />
              <span className="text-sm font-medium text-foreground/80 group-hover:text-foreground transition-colors duration-200 whitespace-nowrap">
                {aid}
              </span>
            </motion.div>
          ))}
        </motion.div>

        {/* Footer note */}
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="text-center text-sm text-muted-foreground mt-10"
        >
          Not sure if your plan is covered?{" "}
          <button
            className="text-primary font-semibold hover:underline underline-offset-2"
            onClick={() => window.open("https://wa.me/27847564715?text=Hi%2C+I%27d+like+to+check+if+my+medical+aid+is+accepted+at+your+practice.", "_blank")}
            data-testid="btn-check-medical-aid"
          >
            WhatsApp us to confirm
          </button>
        </motion.p>
      </div>
    </section>
  );
}
