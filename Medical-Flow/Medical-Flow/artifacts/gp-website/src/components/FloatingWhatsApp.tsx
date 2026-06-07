import { SiWhatsapp } from "react-icons/si";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function FloatingWhatsApp() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const toggleVisibility = () => {
      // Show when scrolled down 300px
      if (window.scrollY > 300) {
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    };

    window.addEventListener("scroll", toggleVisibility);
    return () => window.removeEventListener("scroll", toggleVisibility);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.5, y: 20 }}
      animate={{ 
        opacity: isVisible ? 1 : 0, 
        scale: isVisible ? 1 : 0.5,
        y: isVisible ? 0 : 20,
        pointerEvents: isVisible ? "auto" : "none"
      }}
      transition={{ duration: 0.3 }}
      className="fixed bottom-6 right-6 z-40 hidden md:block" // Hidden on mobile, sticky bar handles it
    >
      <a
        href="https://wa.me/27847564715"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center justify-center w-16 h-16 bg-[#25D366] hover:bg-[#1EBE5D] text-white rounded-full shadow-lg shadow-green-500/30 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group relative"
        aria-label="Chat on WhatsApp"
      >
        <span className="absolute right-full mr-4 bg-white text-slate-800 px-3 py-2 rounded-lg text-sm font-medium shadow-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none before:absolute before:top-1/2 before:left-full before:-translate-y-1/2 before:border-8 before:border-transparent before:border-l-white">
          Need help? Chat with us
        </span>
        <SiWhatsapp className="w-8 h-8" />
        <span className="absolute top-0 right-0 w-4 h-4 bg-red-500 border-2 border-white rounded-full"></span>
      </a>
    </motion.div>
  );
}
