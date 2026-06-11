import { Phone, Calendar } from "lucide-react";
import { SiWhatsapp } from "react-icons/si";

export default function StickyMobileBar() {
  const scrollToBooking = () => {
    document.getElementById('booking')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] pb-safe">
      <div className="flex items-stretch justify-around h-16">
        <a 
          href="tel:+27726033299" 
          className="flex-1 flex flex-col items-center justify-center gap-1 text-slate-600 hover:bg-slate-50 transition-colors active:bg-slate-100"
        >
          <Phone className="w-5 h-5" />
          <span className="text-[10px] font-medium">Call</span>
        </a>
        
        <div className="w-px bg-gray-200 my-2"></div>
        
        <a 
          href="https://wa.me/27726033299" 
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 flex flex-col items-center justify-center gap-1 text-green-600 hover:bg-green-50 transition-colors active:bg-green-100"
        >
          <SiWhatsapp className="w-5 h-5" />
          <span className="text-[10px] font-medium">WhatsApp</span>
        </a>
        
        <div className="w-px bg-gray-200 my-2"></div>
        
        <button 
          onClick={scrollToBooking}
          className="flex-1 flex flex-col items-center justify-center gap-1 text-primary hover:bg-primary/5 transition-colors active:bg-primary/10"
        >
          <Calendar className="w-5 h-5" />
          <span className="text-[10px] font-medium">Book</span>
        </button>
      </div>
    </div>
  );
}
