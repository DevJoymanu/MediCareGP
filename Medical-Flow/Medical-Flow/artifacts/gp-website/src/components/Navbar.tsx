import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Calendar, Phone, X, Menu } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";
import { Button } from "@/components/ui/button";

const navLinks = [
  { label: "Services", href: "#services" },
  { label: "Online Consult", href: "#online-consultation" },
  { label: "Medical Aids", href: "#medical-aids" },
  { label: "Testimonials", href: "#testimonials" },
  { label: "Find Us", href: "#contact" },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuOpen]);

  const scrollTo = (href: string) => {
    setMenuOpen(false);
    const id = href.replace("#", "");
    setTimeout(() => {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    }, menuOpen ? 300 : 0);
  };

  const scrollToBooking = () => scrollTo("#booking");

  return (
    <>
      <motion.header
        initial={{ y: -80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring" as const, stiffness: 220, damping: 26, delay: 0.1 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          scrolled
            ? "bg-white/85 backdrop-blur-md shadow-sm border-b border-black/5"
            : "bg-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">

            {/* Logo / Brand */}
            <button
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              className="flex flex-col items-start leading-tight"
              data-testid="nav-brand"
            >
              <span className="text-base font-bold text-foreground tracking-tight">
                Rand Medical Resources
              </span>
              <span className="text-[11px] text-muted-foreground font-medium tracking-wide">
                General Practitioner · Kwa-Thema
              </span>
            </button>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-1" aria-label="Main navigation">
              {navLinks.map((link) => (
                <button
                  key={link.href}
                  onClick={() => scrollTo(link.href)}
                  className="px-4 py-2 rounded-lg text-sm font-medium text-foreground/70 hover:text-foreground hover:bg-black/5 transition-all duration-200"
                  data-testid={`nav-link-${link.label.toLowerCase().replace(/\s+/g, "-")}`}
                >
                  {link.label}
                </button>
              ))}
            </nav>

            {/* Desktop CTAs */}
            <div className="hidden md:flex items-center gap-2">
              <a
                href="tel:+27847564715"
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-foreground/70 hover:text-foreground hover:bg-black/5 transition-all duration-200"
                data-testid="nav-link-call"
              >
                <Phone className="w-4 h-4" />
                084 756 4715
              </a>
              <a
                href="https://wa.me/27847564715"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium text-green-700 hover:bg-green-50 transition-all duration-200 border border-green-200"
                data-testid="nav-link-whatsapp"
              >
                <SiWhatsapp className="w-4 h-4 text-green-600" />
                WhatsApp
              </a>
              <Button
                size="sm"
                onClick={scrollToBooking}
                className="rounded-full px-5 text-sm shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200"
                data-testid="nav-btn-book"
              >
                <Calendar className="w-4 h-4 mr-1.5" />
                Book Appointment
              </Button>
            </div>

            {/* Hamburger (mobile) */}
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="md:hidden flex items-center justify-center w-10 h-10 rounded-xl hover:bg-black/5 transition-colors"
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
              data-testid="nav-hamburger"
            >
              <AnimatePresence mode="wait" initial={false}>
                {menuOpen ? (
                  <motion.div
                    key="close"
                    initial={{ rotate: -90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: 90, opacity: 0 }}
                    transition={{ duration: 0.18 }}
                  >
                    <X className="w-5 h-5 text-foreground" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="menu"
                    initial={{ rotate: 90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: -90, opacity: 0 }}
                    transition={{ duration: 0.18 }}
                  >
                    <Menu className="w-5 h-5 text-foreground" />
                  </motion.div>
                )}
              </AnimatePresence>
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile drawer */}
      <AnimatePresence>
        {menuOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              key="backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm md:hidden"
              onClick={() => setMenuOpen(false)}
            />

            {/* Slide-down panel */}
            <motion.div
              key="drawer"
              initial={{ opacity: 0, y: -16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ type: "spring" as const, stiffness: 300, damping: 28 }}
              className="fixed top-16 left-0 right-0 z-40 md:hidden bg-white border-b border-black/5 shadow-xl rounded-b-3xl overflow-hidden"
            >
              <nav className="px-4 pt-4 pb-2 space-y-1" aria-label="Mobile navigation">
                {navLinks.map((link, i) => (
                  <motion.button
                    key={link.href}
                    initial={{ opacity: 0, x: -12 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.06 }}
                    onClick={() => scrollTo(link.href)}
                    className="w-full flex items-center px-4 py-3 rounded-xl text-base font-medium text-foreground hover:bg-primary/5 hover:text-primary transition-all duration-200 text-left"
                    data-testid={`mobile-nav-link-${link.label.toLowerCase().replace(/\s+/g, "-")}`}
                  >
                    {link.label}
                  </motion.button>
                ))}
              </nav>

              {/* Mobile contact / CTAs */}
              <div className="px-4 pt-2 pb-6 space-y-3 border-t border-black/5 mt-2">
                <a
                  href="tel:+27847564715"
                  className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-50 text-foreground font-medium hover:bg-gray-100 transition-colors"
                  data-testid="mobile-nav-link-call"
                  onClick={() => setMenuOpen(false)}
                >
                  <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Phone className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Call us</div>
                    <div className="font-semibold">084 756 4715</div>
                  </div>
                </a>

                <a
                  href="https://wa.me/27847564715"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 px-4 py-3 rounded-xl bg-green-50 text-green-800 font-medium hover:bg-green-100 transition-colors"
                  data-testid="mobile-nav-link-whatsapp"
                  onClick={() => setMenuOpen(false)}
                >
                  <div className="w-9 h-9 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    <SiWhatsapp className="w-4 h-4 text-green-600" />
                  </div>
                  <div>
                    <div className="text-xs text-green-600">Message us</div>
                    <div className="font-semibold">WhatsApp Us</div>
                  </div>
                </a>

                <Button
                  className="w-full rounded-xl py-6 text-base shadow-md"
                  onClick={scrollToBooking}
                  data-testid="mobile-nav-btn-book"
                >
                  <Calendar className="w-5 h-5 mr-2" />
                  Book an Appointment
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
