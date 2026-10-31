"use client";

import { useEffect, useRef, useState } from "react";

const lines = [
  ["Every", "AI", "Tool."],
  ["One", "Place."],
];

export function TaglineReveal() {
  const wordRefs = useRef<Array<HTMLSpanElement | null>>([]);
  const [visibleWords, setVisibleWords] = useState<Set<number>>(() => new Set());

  useEffect(() => {
    const motionPreference = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    );
    if (motionPreference.matches) {
      setVisibleWords(new Set(lines.flat().map((_, index) => index)));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        setVisibleWords((previous) => {
          const next = new Set(previous);
          for (const entry of entries) {
            if (entry.isIntersecting) {
              const index = Number(
                (entry.target as HTMLSpanElement).dataset.wordIndex,
              );
              next.add(index);
              observer.unobserve(entry.target);
            }
          }
          return next;
        });
      },
      { rootMargin: "0px 0px -35% 0px", threshold: 0.1 },
    );

    wordRefs.current.forEach((element) => {
      if (element) observer.observe(element);
    });
    return () => observer.disconnect();
  }, []);

  return (
    <section
      aria-label="Every AI Tool. One Place."
      className="mx-auto max-w-6xl px-6 py-24 sm:py-24"
    >
      <p className="heading-2 max-w-3xl text-white">
        {lines.map((line, lineIndex) => (
          <span className="block" key={line.join(" ")}>
            {line.map((word, wordIndex) => {
              const index =
                lines.slice(0, lineIndex).reduce((count, row) => count + row.length, 0) +
                wordIndex;
              return (
                <span
                  className={`tagline-word inline-block ${
                    visibleWords.has(index) ? "is-visible" : ""
                  }`}
                  data-word-index={index}
                  key={word}
                  ref={(element) => {
                    wordRefs.current[index] = element;
                  }}
                  style={{
                    transitionDelay: visibleWords.has(index)
                      ? `${index * 80}ms`
                      : "0ms",
                  }}
                >
                  {word}
                  {wordIndex < line.length - 1 ? "\u00a0" : ""}
                </span>
              );
            })}
          </span>
        ))}
      </p>
    </section>
  );
}
