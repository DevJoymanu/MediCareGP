import { useState, useEffect, useRef } from "react";

export function useInView(options: IntersectionObserverInit = { threshold: 0.1 }) {
  const [isInView, setIsInView] = useState(false);
  const ref = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsInView(true);
        // Once visible, we can optionally stop observing if we only want to trigger once
        if (ref.current) {
          observer.unobserve(ref.current);
        }
      }
    }, options);

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current);
      }
    };
  }, [options.threshold, options.root, options.rootMargin]);

  return { ref, isInView };
}
