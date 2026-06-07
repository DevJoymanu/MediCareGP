import { motion } from "framer-motion";
import { useInView } from "@/hooks/useInView";
import { useCountUp } from "@/hooks/useCountUp";

function StatCard({ end, label, suffix = "", duration = 2000, start = false }: { end: number, label: string, suffix?: string, duration?: number, start?: boolean }) {
  const count = useCountUp(end, duration, start);
  
  return (
    <div className="flex flex-col items-center justify-center p-6 bg-white rounded-2xl shadow-sm border border-black/5 hover:shadow-md transition-shadow">
      <div className="text-4xl md:text-5xl font-bold text-primary mb-2 flex items-center">
        {count}
        {suffix && <span className="text-3xl md:text-4xl">{suffix}</span>}
      </div>
      <div className="text-sm md:text-base font-medium text-muted-foreground text-center">
        {label}
      </div>
    </div>
  );
}

export default function TrustStats() {
  const { ref, isInView } = useInView({ threshold: 0.3 });

  return (
    <section ref={ref} className="py-12 bg-white relative z-10 -mt-8 mx-4 sm:mx-8 lg:mx-auto max-w-6xl rounded-3xl shadow-lg border border-black/5">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8">
          <StatCard end={25} suffix="+" label="Years Experience" start={isInView} />
          <StatCard end={15} suffix="k+" label="Patients Helped" start={isInView} duration={2500} />
          <div className="flex flex-col items-center justify-center p-6 bg-primary/5 rounded-2xl border border-primary/10">
            <div className="w-12 h-12 mb-3 bg-white rounded-full flex items-center justify-center shadow-sm text-primary">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <div className="text-sm md:text-base font-bold text-foreground text-center">HPCSA Registered</div>
          </div>
          <div className="flex flex-col items-center justify-center p-6 bg-accent/10 rounded-2xl border border-accent/20">
            <div className="w-12 h-12 mb-3 bg-white rounded-full flex items-center justify-center shadow-sm text-accent">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <div className="text-sm md:text-base font-bold text-foreground text-center">Same-Day Booking</div>
          </div>
        </div>
      </div>
    </section>
  );
}
