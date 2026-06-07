import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import TrustStats from "@/components/TrustStats";
import Services from "@/components/Services";
import OnlineConsultation from "@/components/OnlineConsultation";
import MedicalAids from "@/components/MedicalAids";
import BookingForm from "@/components/BookingForm";
import Testimonials from "@/components/Testimonials";
import FAQ from "@/components/FAQ";
import Location from "@/components/Location";
import Footer from "@/components/Footer";
import StickyMobileBar from "@/components/StickyMobileBar";
import FloatingWhatsApp from "@/components/FloatingWhatsApp";
import BookingSuccessModal from "@/components/BookingSuccessModal";

export default function Home() {
  return (
    <div className="flex flex-col min-h-[100dvh] w-full overflow-x-hidden bg-background text-foreground">
      <Navbar />
      <main className="flex-1 w-full relative z-0">
        <Hero />
        <TrustStats />
        <Services />
        <OnlineConsultation />
        <MedicalAids />
        <div id="booking">
          <BookingForm />
        </div>
        <Testimonials />
        <FAQ />
        <Location />
      </main>
      <Footer />
      <StickyMobileBar />
      <FloatingWhatsApp />
      <BookingSuccessModal />
    </div>
  );
}
