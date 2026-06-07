import { MapPin, Clock, Phone } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";
import { motion } from "framer-motion";
import { useInView } from "@/hooks/useInView";

const WHATSAPP = "https://wa.me/27847564715";
const TEL = "tel:+27847564715";

export default function Location() {
  const { ref, isInView } = useInView({ threshold: 0.2 });

  return (
    <section className="py-24 bg-gray-50" id="contact" ref={ref}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">

          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -30 }}
            transition={{ duration: 0.6 }}
            className="space-y-8"
          >
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">Visit Our Practice</h2>
              <p className="text-lg text-muted-foreground">
                Conveniently located inside Ekhaya Mall in Kwa-Thema, Springs. We offer a comfortable, welcoming environment for all your healthcare needs.
              </p>
            </div>

            <div className="space-y-4">
              {/* Address */}
              <div className="flex items-start gap-4 p-5 rounded-2xl bg-white border border-black/5 shadow-sm">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <MapPin className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-1">Address</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    Shop B7, Ekhaya Medical Centre<br />
                    Ekhaya Mall, Kwa-Thema<br />
                    Springs, Gauteng<br />
                    South Africa
                  </p>
                  <a
                    href="https://maps.google.com/?q=Ekhaya+Mall+Kwa-Thema+Springs"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-3 text-sm text-primary font-semibold hover:underline underline-offset-2"
                    data-testid="link-get-directions"
                  >
                    <MapPin className="w-4 h-4" />
                    Get Directions
                  </a>
                </div>
              </div>

              {/* Hours */}
              <div className="flex items-start gap-4 p-5 rounded-2xl bg-white border border-black/5 shadow-sm">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Clock className="w-6 h-6 text-primary" />
                </div>
                <div className="w-full">
                  <h3 className="font-bold text-lg mb-3">Consulting Hours</h3>
                  <div className="space-y-2 text-muted-foreground">
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-foreground">Monday – Friday</span>
                      <span className="bg-primary/10 text-primary text-sm font-semibold px-3 py-0.5 rounded-full">09:30 – 18:00</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="font-medium text-foreground">Saturday – Sunday</span>
                      <span className="bg-primary/10 text-primary text-sm font-semibold px-3 py-0.5 rounded-full">09:30 – 13:00</span>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-sm text-muted-foreground">Walk-ins welcome, subject to availability</span>
                  </div>
                </div>
              </div>

              {/* Contact */}
              <div className="flex items-start gap-4 p-5 rounded-2xl bg-white border border-black/5 shadow-sm">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Phone className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-2">Contact</h3>
                  <div className="space-y-2">
                    <a
                      href={TEL}
                      className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
                      data-testid="link-phone"
                    >
                      <Phone className="w-4 h-4 flex-shrink-0" />
                      084 756 4715
                    </a>
                    <a
                      href={WHATSAPP}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-muted-foreground hover:text-green-600 transition-colors"
                      data-testid="link-whatsapp"
                    >
                      <SiWhatsapp className="w-4 h-4 flex-shrink-0 text-green-500" />
                      WhatsApp: 084 756 4715
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Map */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: 30 }}
            transition={{ duration: 0.6 }}
            className="h-[520px] w-full rounded-3xl overflow-hidden shadow-lg border border-black/5"
          >
            <iframe
              title="Practice Location"
              src="https://maps.google.com/maps?q=Ekhaya+Mall+Kwa-Thema+Springs+Gauteng&output=embed"
              width="100%"
              height="100%"
              style={{ border: 0 }}
              allowFullScreen
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              data-testid="iframe-map"
            />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
