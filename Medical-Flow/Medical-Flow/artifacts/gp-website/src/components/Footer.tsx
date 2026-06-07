import { Heart, MapPin, Phone, Clock } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";

const WHATSAPP = "https://wa.me/27847564715";
const TEL = "tel:+27847564715";

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 py-12 pb-24 md:pb-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">

          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-xl font-bold text-white mb-1">Rand Medical Resources</h3>
            <p className="text-slate-500 text-sm mb-4">General Practitioner · PTY (LTD)</p>
            <p className="text-slate-400 max-w-sm mb-5 leading-relaxed text-sm">
              Providing compassionate, comprehensive healthcare to the communities of Kwa-Thema, Springs, and the East Rand.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center px-3 py-1 rounded-full bg-slate-800 text-xs font-medium border border-slate-700">
                HPCSA Registered
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full bg-slate-800 text-xs font-medium border border-slate-700">
                BHF Registered
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full bg-slate-800 text-xs font-medium border border-slate-700">
                Medical Aid Accepted
              </span>
            </div>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-white font-bold mb-4 uppercase tracking-wider text-xs">Contact</h4>
            <ul className="space-y-3 text-sm">
              <li>
                <a href={TEL} className="flex items-center gap-2 hover:text-white transition-colors" data-testid="footer-link-phone">
                  <Phone className="w-4 h-4 flex-shrink-0" />
                  084 756 4715
                </a>
              </li>
              <li>
                <a href={WHATSAPP} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-green-400 transition-colors" data-testid="footer-link-whatsapp">
                  <SiWhatsapp className="w-4 h-4 flex-shrink-0 text-green-500" />
                  WhatsApp Us
                </a>
              </li>
              <li>
                <a
                  href="https://maps.google.com/?q=Ekhaya+Mall+Kwa-Thema+Springs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start gap-2 hover:text-white transition-colors"
                  data-testid="footer-link-address"
                >
                  <MapPin className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>Shop B7, Ekhaya Medical Centre,<br />Ekhaya Mall, Kwa-Thema, Springs</span>
                </a>
              </li>
              <li className="flex items-start gap-2">
                <Clock className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>Mon–Fri: 09:30–18:00<br />Sat–Sun: 09:30–13:00</span>
              </li>
            </ul>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-white font-bold mb-4 uppercase tracking-wider text-xs">Quick Links</h4>
            <ul className="space-y-3 text-sm">
              <li><a href="#services" className="hover:text-white transition-colors">Services</a></li>
              <li><a href="#medical-aids" className="hover:text-white transition-colors">Medical Aids</a></li>
              <li><a href="#booking" className="hover:text-white transition-colors">Book Appointment</a></li>
              <li><a href="#contact" className="hover:text-white transition-colors">Find Us</a></li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-slate-500">
          <p>© {new Date().getFullYear()} Rand Medical Resources PTY (LTD). All rights reserved.</p>
          <p className="flex items-center gap-1">
            Built with <Heart className="w-4 h-4 text-red-500 mx-1" /> for patient care
          </p>
        </div>
      </div>
    </footer>
  );
}
