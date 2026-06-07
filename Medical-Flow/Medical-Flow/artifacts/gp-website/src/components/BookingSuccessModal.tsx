import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, X, Calendar, Video } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function BookingSuccessModal() {
  const [open, setOpen] = useState(false);
  const [ref, setRef] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("booking") === "requested") {
      setOpen(true);
      setRef(params.get("ref"));
      // Clean the URL without reloading.
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const dismiss = () => setOpen(false);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={dismiss}
            className="fixed inset-0 bg-black/40 z-[100] backdrop-blur-sm"
          />
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.85, y: 40 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: "spring", stiffness: 260, damping: 22 }}
            className="fixed inset-0 z-[101] flex items-center justify-center p-4 pointer-events-none"
          >
            <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full pointer-events-auto relative">
              <button
                onClick={dismiss}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex flex-col items-center text-center gap-4">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 220, delay: 0.15 }}
                  className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center"
                >
                  <CheckCircle className="w-10 h-10 text-green-600" />
                </motion.div>
                <div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">Booking Request Received</h2>
                  <p className="text-muted-foreground leading-relaxed">
                    Thanks! We've received your appointment request. We'll contact you to confirm the time and any details.
                  </p>
                  {ref && (
                    <div className="mt-3 inline-flex items-center gap-2 bg-gray-50 rounded-xl px-4 py-2 text-sm">
                      <span className="text-muted-foreground">Booking ref:</span>
                      <span className="font-bold text-foreground font-mono">{ref}</span>
                    </div>
                  )}
                </div>
                <div className="w-full space-y-3 pt-2">
                  <div className="flex items-start gap-3 text-sm text-left bg-primary/5 rounded-xl p-4">
                    <Calendar className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                    <span>We will contact you to confirm your appointment time. Please keep your phone nearby.</span>
                  </div>
                  <div className="flex items-start gap-3 text-sm text-left bg-blue-50 rounded-xl p-4">
                    <Video className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                    <span>If you booked an online consultation, we'll send you a private, secure video link before your appointment — it opens right in your browser.</span>
                  </div>
                </div>
                <Button onClick={dismiss} className="w-full rounded-xl mt-1">
                  Done
                </Button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
