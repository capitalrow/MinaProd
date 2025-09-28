import { useState } from "react";
import { motion } from "framer-motion";

// Mina Animated Splash Logo
// - Squircle background with breathing glow
// - Mic/M bars with pulsing heights + shimmer sweep
// - Gloss reflection glide
// - Wordmark fade-in with shine sweep

const ACCENTS = {
  purple: {
    name: "Premium Purple",
    gradient: ["#C084FC", "#9333EA", "#4C1D95"],
    neon: "#A855F7",
  },
  blue: {
    name: "Clarity Blue",
    gradient: ["#7CC4FF", "#3B82F6", "#1E3A8A"],
    neon: "#3B82F6",
  },
  mono: {
    name: "Monochrome",
    gradient: ["#F3F4F6", "#6B7280", "#111827"],
    neon: "#9CA3AF",
  },
};

function gradientCSS(direction, stops) {
  return { background: `linear-gradient(${direction}, ${stops.join(", ")})` };
}

function MicSymbolAnimated({ accent = ACCENTS.purple, size = 128 }) {
  const barW = Math.round(size * 0.18);
  const barH = Math.round(size * 0.65);
  const gap = Math.round(barW * 0.65);
  const horizH = Math.max(2, Math.round(size * 0.12));
  const horizW = Math.round(size * 0.85);

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      {/* Horizontal connector behind */}
      <motion.div
        className="absolute"
        style={{
          width: horizW,
          height: horizH,
          borderRadius: horizH,
          background: `linear-gradient(90deg, ${accent.gradient[0]}, ${accent.gradient[2]})`,
          boxShadow: "0 2px 6px rgba(0,0,0,0.5) inset, 0 2px 4px rgba(255,255,255,0.25)",
          opacity: 0.9,
        }}
        animate={{ opacity: [0.8, 1, 0.8] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Three bars forming M — animated pulse + shimmer */}
      <div className="relative z-10 flex items-end" style={{ gap }}>
        {[1, 0.75, 1].map((scale, i) => (
          <motion.div
            key={i}
            className="relative overflow-hidden"
            style={{
              width: barW,
              height: barH,
              borderRadius: barW,
              ...gradientCSS("180deg", [accent.gradient[0], accent.gradient[1], accent.gradient[2], accent.gradient[1]]),
              boxShadow:
                `inset 0 3px 6px rgba(255,255,255,0.5), inset 0 -4px 8px rgba(0,0,0,0.6), 0 8px 16px rgba(0,0,0,0.4), 0 0 16px ${accent.neon}88`,
            }}
            animate={{ height: [barH * scale * 0.9, barH * scale * 1.05, barH * scale * 0.9] }}
            transition={{ duration: 2 + i * 0.3, repeat: Infinity, ease: "easeInOut", delay: i * 0.3 }}
          >
            {/* Shimmer sweep */}
            <motion.div
              className="absolute -inset-y-6 -left-14 h-[220%] w-14 rotate-12"
              style={{
                background:
                  "linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.35), rgba(255,255,255,0))",
                filter: "blur(0.6px)",
              }}
              animate={{ x: [-(size * 0.9), size * 0.9] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut", delay: i * 0.4 }}
            />
          </motion.div>
        ))}
      </div>

      {/* Gloss reflection glide across top */}
      <motion.div
        className="pointer-events-none absolute top-0 left-0 right-0 h-1/2 rounded-t-full"
        style={{
          background: "linear-gradient(to bottom, rgba(255,255,255,0.55), rgba(255,255,255,0))",
          mixBlendMode: "screen",
        }}
        animate={{ opacity: [0.85, 0.5, 0.85] }}
        transition={{ duration: 6.5, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}

function AppIconAnimated({ accent = ACCENTS.purple, size = 200 }) {
  const radius = size * 0.25;
  return (
    <motion.div
      className="flex items-center justify-center"
      style={{
        width: size,
        height: size,
        borderRadius: radius,
        background: `radial-gradient(circle at 30% 30%, ${accent.gradient[0]}, ${accent.gradient[1]}, ${accent.gradient[2]})`,
        boxShadow: `0 0 30px ${accent.neon}88, 0 0 60px ${accent.neon}44, inset 0 2px 4px rgba(255,255,255,0.2)`,
      }}
      animate={{ scale: [1, 1.05, 1] }}
      transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
    >
      <MicSymbolAnimated accent={accent} size={size * 0.55} />
    </motion.div>
  );
}

function WordmarkAnimated({ accent = ACCENTS.purple, size = 72 }) {
  const height = size * 1.25;
  return (
    <div className="relative select-none mt-6">
      <motion.span
        className="font-extrabold tracking-tight"
        style={{
          fontSize: size,
          background: `linear-gradient(90deg, ${accent.gradient[0]}, ${accent.gradient[1]}, ${accent.gradient[2]})`,
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          textShadow: `0 0 18px ${accent.neon}66, 0 2px 10px rgba(0,0,0,0.2)`,
        }}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1.8, ease: "easeOut" }}
      >
        Mina
      </motion.span>
      {/* Shine sweep */}
      <motion.div
        className="absolute top-0 left-0 h-full w-full"
        style={{
          background:
            "linear-gradient(120deg, rgba(255,255,255,0), rgba(255,255,255,0.7), rgba(255,255,255,0))",
          WebkitMaskImage: "linear-gradient(90deg, rgba(0,0,0,1), rgba(0,0,0,0))",
          mixBlendMode: "overlay",
        }}
        animate={{ x: [-(size * 2), size * 2] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 2 }}
      />
    </div>
  );
}

export default function MinaSplashLogo() {
  const [theme, setTheme] = useState("purple");
  const accent = ACCENTS[theme];

  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-gray-950 to-gray-900 text-center p-8">
      <AppIconAnimated accent={accent} size={220} />
      <WordmarkAnimated accent={accent} size={80} />
    </div>
  );
}
