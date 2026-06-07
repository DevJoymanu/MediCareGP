import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { motion } from "framer-motion";
import { useInView } from "@/hooks/useInView";

const faqs = [
  {
    question: "Do you accept walk-ins?",
    answer: "Yes, walk-ins are welcome subject to availability. Booking in advance is recommended for guaranteed time slots."
  },
  {
    question: "Are you HPCSA registered?",
    answer: "Yes, fully registered with the Health Professions Council of South Africa."
  },
  {
    question: "Do you issue sick notes?",
    answer: "Yes, we issue sick notes, medical certificates, and insurance certificates after a thorough medical consultation."
  },
  {
    question: "What are your consulting hours?",
    answer: "Monday to Friday 09:30–18:00, Saturday and Sunday 09:30–13:00. Walk-ins welcome subject to availability."
  },
  {
    question: "Do you see children?",
    answer: "Yes, we see patients of all ages including pediatric consultations and routine check-ups."
  },
  {
    question: "Can I get a prescription refill?",
    answer: "Yes, chronic medication renewals are available — please call ahead or book a brief consultation."
  }
];

export default function FAQ() {
  const { ref, isInView } = useInView({ threshold: 0.2 });

  return (
    <section className="py-24 bg-white" ref={ref}>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">Common Questions</h2>
          <p className="text-lg text-muted-foreground">
            Everything you need to know about our practice and services.
          </p>
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-3xl p-6 md:p-8 shadow-sm border border-black/5"
        >
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`item-${index}`} className="border-b-black/5">
                <AccordionTrigger className="text-left text-lg font-medium hover:text-primary transition-colors py-4">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground text-base leading-relaxed pb-4">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
        
        <div className="mt-12 text-center">
          <p className="text-muted-foreground mb-4">Still have questions?</p>
          <a 
            href="https://wa.me/27847564715" 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center text-primary font-medium hover:underline"
          >
            Ask us on WhatsApp
          </a>
        </div>
      </div>
    </section>
  );
}
