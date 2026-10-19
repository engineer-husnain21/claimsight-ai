"use client";

import { useEffect, useRef } from "react";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
}

interface Pointer {
  x: number;
  y: number;
  active: boolean;
}

const COLORS = ["#22d3ee", "#a78bfa", "#f472b6", "#60a5fa"] as const;
const LINK_DISTANCE = 140;
const POINTER_LINK_DISTANCE = 190;
const POINTER_PUSH_STRENGTH = 0.6;
const AREA_PER_PARTICLE = 11_000;
const MAX_PARTICLES = 150;
const MAX_SPEED = 0.35;
const MAX_PIXEL_RATIO = 2;

function randomBetween(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

function createParticles(width: number, height: number): Particle[] {
  const count = Math.min(MAX_PARTICLES, Math.floor((width * height) / AREA_PER_PARTICLE));
  return Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: randomBetween(-MAX_SPEED, MAX_SPEED),
    vy: randomBetween(-MAX_SPEED, MAX_SPEED),
    radius: randomBetween(1, 2.4),
    color: COLORS[Math.floor(Math.random() * COLORS.length)],
  }));
}

function moveParticle(particle: Particle, width: number, height: number, pointer: Pointer): void {
  if (pointer.active) {
    const dx = particle.x - pointer.x;
    const dy = particle.y - pointer.y;
    const distance = Math.hypot(dx, dy);
    if (distance > 0 && distance < POINTER_LINK_DISTANCE / 2) {
      const force = (1 - distance / (POINTER_LINK_DISTANCE / 2)) * POINTER_PUSH_STRENGTH;
      particle.x += (dx / distance) * force;
      particle.y += (dy / distance) * force;
    }
  }

  particle.x += particle.vx;
  particle.y += particle.vy;

  if (particle.x < 0 || particle.x > width) {
    particle.vx *= -1;
    particle.x = Math.min(Math.max(particle.x, 0), width);
  }
  if (particle.y < 0 || particle.y > height) {
    particle.vy *= -1;
    particle.y = Math.min(Math.max(particle.y, 0), height);
  }
}

function drawFrame(
  context: CanvasRenderingContext2D,
  particles: Particle[],
  width: number,
  height: number,
  pointer: Pointer,
): void {
  context.clearRect(0, 0, width, height);
  context.lineWidth = 0.8;

  for (let i = 0; i < particles.length; i += 1) {
    const a = particles[i];
    for (let j = i + 1; j < particles.length; j += 1) {
      const b = particles[j];
      const distance = Math.hypot(a.x - b.x, a.y - b.y);
      if (distance < LINK_DISTANCE) {
        const gradient = context.createLinearGradient(a.x, a.y, b.x, b.y);
        gradient.addColorStop(0, a.color);
        gradient.addColorStop(1, b.color);
        context.globalAlpha = (1 - distance / LINK_DISTANCE) * 0.45;
        context.strokeStyle = gradient;
        context.beginPath();
        context.moveTo(a.x, a.y);
        context.lineTo(b.x, b.y);
        context.stroke();
      }
    }

    if (pointer.active) {
      const distance = Math.hypot(a.x - pointer.x, a.y - pointer.y);
      if (distance < POINTER_LINK_DISTANCE) {
        context.globalAlpha = (1 - distance / POINTER_LINK_DISTANCE) * 0.7;
        context.strokeStyle = a.color;
        context.beginPath();
        context.moveTo(a.x, a.y);
        context.lineTo(pointer.x, pointer.y);
        context.stroke();
      }
    }
  }

  context.globalAlpha = 1;
  context.shadowBlur = 8;
  for (const particle of particles) {
    context.shadowColor = particle.color;
    context.fillStyle = particle.color;
    context.beginPath();
    context.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
    context.fill();
  }
  context.shadowBlur = 0;
}

/** Full-screen animated particle network. Purely decorative and hidden from screen readers. */
export function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) {
      return;
    }

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const pointer: Pointer = { x: 0, y: 0, active: false };
    let width = 0;
    let height = 0;
    let particles: Particle[] = [];
    let frameId: number | null = null;

    const resize = (): void => {
      const pixelRatio = Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * pixelRatio);
      canvas.height = Math.floor(height * pixelRatio);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      particles = createParticles(width, height);
      drawFrame(context, particles, width, height, pointer);
    };

    const step = (): void => {
      for (const particle of particles) {
        moveParticle(particle, width, height, pointer);
      }
      drawFrame(context, particles, width, height, pointer);
      frameId = window.requestAnimationFrame(step);
    };

    const start = (): void => {
      if (!reducedMotion && frameId === null) {
        frameId = window.requestAnimationFrame(step);
      }
    };

    const stop = (): void => {
      if (frameId !== null) {
        window.cancelAnimationFrame(frameId);
        frameId = null;
      }
    };

    const handlePointerMove = (event: PointerEvent): void => {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointer.active = true;
    };

    const handlePointerLeave = (): void => {
      pointer.active = false;
    };

    const handleVisibilityChange = (): void => {
      if (document.hidden) {
        stop();
      } else {
        start();
      }
    };

    resize();
    start();

    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", handlePointerMove);
    document.documentElement.addEventListener("pointerleave", handlePointerLeave);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      stop();
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", handlePointerMove);
      document.documentElement.removeEventListener("pointerleave", handlePointerLeave);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgba(34,211,238,0.18),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(167,139,250,0.2),transparent_55%),radial-gradient(ellipse_at_center,rgba(244,114,182,0.08),transparent_60%)]" />
      <canvas ref={canvasRef} className="absolute inset-0" />
    </div>
  );
}