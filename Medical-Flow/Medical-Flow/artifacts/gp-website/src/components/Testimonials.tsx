import { useRef, useEffect } from "react";
import { motion, useAnimation, useInView } from "framer-motion";
import { Star, Quote } from "lucide-react";

const testimonials = [
  {
    text: "Dr. has been our family doctor for over 15 years. Incredibly caring, always thorough, never rushes you.",
    author: "Nomvula S.",
    location: "Kwa-Thema"
  },
  {
    text: "Got a same-day appointment when my daughter had a high fever. So relieved to have a doctor like this nearby.",
    author: "Thabo M.",
    location: "Springs"
  },
  {
    text: "Professional, compassionate, and always explains everything clearly. HPCSA registered and it shows.",
    author: "Priya N.",
    location: "Benoni"
  },
  {
    text: "I've moved twice but still drive to this practice. The level of care is simply unmatched.",
    author: "James V.",
    location: "East Rand"
  },
  {
    text: "Best GP in Springs. Always makes you feel at ease from the moment you walk in.",
    author: "Zanele D.",
    location: "Kwa-Thema"
  }
];

export default function Testimonials() {
  const containerRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(containerRef, { once: true, margin: "-100px" });
  const controls = useAnimation();

  useEffect(() => {
    if (isInView) {
      controls.start("visible");
    }
  }, [isInView, controls]);

  return (
    <section id="testimonials" className="py-24 bg-primary/5 relative overflow-hidden" ref={containerRef}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">Patient Stories</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Don't just take our word for it. Here's what our patients have to say about their care.
          </p>
        </div>

        {/* CSS-based infinite scroll for smoothness */}
        <div className="relative w-full overflow-hidden flex [mask-image:linear-gradient(to_right,transparent,black_10%,black_90%,transparent)]">
          <div className="flex animate-[scroll_40s_linear_infinite] hover:[animation-play-state:paused]">
            {[...testimonials, ...testimonials].map((testimonial, i) => (
              <div 
                key={i} 
                className="w-[350px] md:w-[450px] flex-shrink-0 px-4"
              >
                <div className="bg-white p-8 rounded-3xl shadow-sm border border-black/5 h-full flex flex-col glass-card relative">
                  <Quote className="absolute top-6 right-6 text-primary/10 w-12 h-12" />
                  <div className="flex gap-1 mb-4">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star key={star} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-foreground/80 text-lg flex-grow mb-6 relative z-10 font-serif italic">
                    "{testimonial.text}"
                  </p>
                  <div className="mt-auto flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold">
                      {testimonial.author.charAt(0)}
                    </div>
                    <div>
                      <div className="font-bold text-foreground">{testimonial.author}</div>
                      <div className="text-sm text-muted-foreground">{testimonial.location}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(calc(-350px * 5 - 20px * 5)); }
        }
        @media (min-width: 768px) {
          @keyframes scroll {
            0% { transform: translateX(0); }
            100% { transform: translateX(calc(-450px * 5 - 32px * 5)); }
          }
        }
      `}} />
    </section>
  );
}
