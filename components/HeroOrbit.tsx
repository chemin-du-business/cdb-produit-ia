"use client";

import { motion } from "framer-motion";

const TIKTOK_ICON = (
  <svg viewBox="0 0 24 24" className="h-5 w-5 fill-white">
    <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.19 8.19 0 0 0 4.79 1.53V6.77a4.85 4.85 0 0 1-1.02-.08z" />
  </svg>
);

// 6 logos espacés uniformément à 60° — départ -90° (top), sens horaire
const SOURCES = [
  {
    label: "TikTok",
    color: "bg-black",
    glow: "shadow-[0_0_20px_rgba(255,255,255,0.15)]",
    icon: TIKTOK_ICON,
    angle: -90, radius: 148,
  },
  {
    label: "Amazon",
    color: "bg-[#FF9900]",
    glow: "shadow-[0_0_20px_rgba(255,153,0,0.4)]",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5 fill-white">
        <path d="M13.958 10.09c0 1.232.029 2.256-.591 3.351-.502.891-1.301 1.438-2.186 1.438-1.214 0-1.922-.924-1.922-2.292 0-2.692 2.415-3.182 4.699-3.182v.685zm3.186 7.705c-.209.189-.512.201-.745.074-1.047-.872-1.233-1.276-1.814-2.106-1.734 1.767-2.962 2.297-5.209 2.297-2.66 0-4.731-1.641-4.731-4.925 0-2.565 1.391-4.309 3.37-5.164 1.715-.754 4.11-.891 5.942-1.098v-.41c0-.753.06-1.642-.383-2.294-.385-.578-1.124-.816-1.776-.816-1.207 0-2.284.618-2.548 1.9-.054.285-.264.567-.549.582l-3.061-.331c-.259-.058-.548-.266-.472-.66C5.516 2.636 8.246 1.5 10.864 1.5c1.344 0 3.099.359 4.158 1.378 1.344 1.258 1.218 2.939 1.218 4.769v4.323c0 1.299.539 1.869 1.047 2.57.179.251.219.551-.01.736l-2.133 1.519zM21.746 19.5c-2.978 2.17-7.286 3.325-10.996 3.325-5.207 0-9.892-1.924-13.44-5.124-.279-.251-.029-.594.306-.399 3.828 2.228 8.556 3.571 13.44 3.571 3.296 0 6.919-.684 10.254-2.1.504-.214.927.33.436.727zm1.247-1.42c-.38-.488-2.513-.231-3.471-.116-.291.035-.336-.218-.073-.402 1.698-1.194 4.487-.849 4.812-.449.325.401-.085 3.198-1.681 4.532-.245.205-.479.096-.369-.175.359-.895 1.162-2.902.782-3.39z"/>
      </svg>
    ),
    angle: -18, radius: 148,
  },
  {
    label: "Meta",
    color: "bg-[#1877F2]",
    glow: "shadow-[0_0_20px_rgba(24,119,242,0.4)]",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5 fill-white">
        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
      </svg>
    ),
    angle: 54, radius: 148,
  },
  {
    label: "Google",
    color: "bg-white",
    glow: "shadow-[0_0_20px_rgba(255,255,255,0.15)]",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
    ),
    angle: 126, radius: 148,
  },
  {
    label: "Trends",
    color: "bg-emerald-500",
    glow: "shadow-[0_0_20px_rgba(16,185,129,0.4)]",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
        <polyline points="17 6 23 6 23 12" />
      </svg>
    ),
    angle: 162, radius: 148,
  },
];

const SIZE = 380;
const CX = SIZE / 2;
const CY = SIZE / 2;

export default function HeroOrbit() {
  return (
    <div
      className="relative flex shrink-0 items-center justify-center"
      style={{ width: SIZE, height: SIZE }}
    >
      {/* Outer glow ring */}
      <div
        className="absolute rounded-full"
        style={{
          width: SIZE * 0.9,
          height: SIZE * 0.9,
          background: "radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 70%)",
        }}
      />

      {/* Orbit ring */}
      <svg className="absolute inset-0" width={SIZE} height={SIZE} style={{ pointerEvents: "none" }}>
        <circle
          cx={CX} cy={CY} r={148}
          fill="none"
          stroke="url(#orbitGrad)"
          strokeWidth="1"
          strokeDasharray="6 5"
          opacity="0.3"
        />
        <defs>
          <linearGradient id="orbitGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="50%" stopColor="#f97316" />
            <stop offset="100%" stopColor="#8b5cf6" />
          </linearGradient>
        </defs>
      </svg>

      {/* Connecting lines */}
      <svg className="absolute inset-0" width={SIZE} height={SIZE} style={{ pointerEvents: "none" }}>
        {SOURCES.map((src) => {
          const rad = (src.angle * Math.PI) / 180;
          const x2 = CX + Math.cos(rad) * src.radius;
          const y2 = CY + Math.sin(rad) * src.radius;
          return (
            <motion.line
              key={src.label}
              x1={CX} y1={CY} x2={x2} y2={y2}
              stroke="url(#lineGrad)"
              strokeWidth="1"
              strokeOpacity="0.2"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1, delay: 0.5 }}
            />
          );
        })}
        <defs>
          <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#f97316" stopOpacity="0.1" />
          </linearGradient>
        </defs>
      </svg>

      {/* Center */}
      <motion.div
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.7, ease: [0.34, 1.56, 0.64, 1] }}
        className="relative z-10 flex h-28 w-28 flex-col items-center justify-center rounded-3xl border border-white/10 bg-white/[0.06] backdrop-blur-sm"
        style={{ boxShadow: "0 0 60px rgba(139,92,246,0.25), inset 0 1px 0 rgba(255,255,255,0.08)" }}
      >
        {/* Pulse ring */}
        <motion.div
          className="absolute inset-0 rounded-3xl border border-violet-500/40"
          animate={{ scale: [1, 1.12, 1], opacity: [0.6, 0, 0.6] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
        />
        <div className="text-2xl">🔎</div>
        <div className="mt-1.5 text-center text-[10px] font-bold leading-tight text-white/60">
          Produit<br />détecté
        </div>
      </motion.div>

      {/* Orbiting logos */}
      {SOURCES.map((src, i) => {
        const rad = (src.angle * Math.PI) / 180;
        const x = CX + Math.cos(rad) * src.radius;
        const y = CY + Math.sin(rad) * src.radius;

        return (
          <motion.div
            key={src.label}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.3 + i * 0.1, ease: [0.34, 1.56, 0.64, 1] }}
            style={{
              position: "absolute",
              left: x,
              top: y,
              transform: "translate(-50%, -50%)",
            }}
          >
            <motion.div
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 3 + i * 0.5, repeat: Infinity, ease: "easeInOut", delay: i * 0.7 }}
              className={`flex h-12 w-12 items-center justify-center rounded-2xl ${src.color} ${src.glow}`}
              title={src.label}
            >
              {src.icon}
            </motion.div>
          </motion.div>
        );
      })}
    </div>
  );
}
