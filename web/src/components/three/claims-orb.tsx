"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import { AdditiveBlending, Color, type Group, type Mesh } from "three";

export interface OrbSegment {
  color: string;
  count: number;
}

const TOTAL_DOTS = 90;
const EMPTY_COLOR = "#64748b";
const GOLDEN_ANGLE = 2.399963;

/** Splits a fixed number of dots across segments, proportional to their counts. */
function distributeDots(segments: OrbSegment[]): string[] {
  const total = segments.reduce((sum, segment) => sum + segment.count, 0);
  if (total === 0) {
    return Array.from({ length: TOTAL_DOTS }, () => EMPTY_COLOR);
  }
  const colors: string[] = [];
  for (const segment of segments) {
    const share = Math.round((segment.count / total) * TOTAL_DOTS);
    for (let index = 0; index < share; index += 1) {
      colors.push(segment.color);
    }
  }
  return colors.slice(0, TOTAL_DOTS);
}

function Core({ animate }: { animate: boolean }) {
  const shellRef = useRef<Mesh>(null);

  useFrame((_, delta) => {
    if (animate && shellRef.current !== null) {
      shellRef.current.rotation.y += delta * 0.25;
      shellRef.current.rotation.x += delta * 0.1;
    }
  });

  return (
    <group>
      <mesh ref={shellRef}>
        <icosahedronGeometry args={[1, 1]} />
        <meshBasicMaterial color="#a78bfa" wireframe transparent opacity={0.55} />
      </mesh>
      <mesh>
        <sphereGeometry args={[0.6, 32, 32]} />
        <meshBasicMaterial
          color="#22d3ee"
          transparent
          opacity={0.22}
          blending={AdditiveBlending}
          depthWrite={false}
        />
      </mesh>
    </group>
  );
}

function OrbitDots({ segments, animate }: { segments: OrbSegment[]; animate: boolean }) {
  const groupRef = useRef<Group>(null);

  const { positions, colors } = useMemo(() => {
    const dotColors = distributeDots(segments);
    const positionArray = new Float32Array(dotColors.length * 3);
    const colorArray = new Float32Array(dotColors.length * 3);
    const color = new Color();

    // Deterministic layout (no randomness) so every render looks the same.
    dotColors.forEach((hex, index) => {
      const angle = index * GOLDEN_ANGLE;
      const radius = 1.6 + ((index * 37) % 10) / 20;
      positionArray[index * 3] = Math.cos(angle) * radius;
      positionArray[index * 3 + 1] = Math.sin(index * 1.3) * 0.35;
      positionArray[index * 3 + 2] = Math.sin(angle) * radius;
      color.set(hex);
      colorArray[index * 3] = color.r;
      colorArray[index * 3 + 1] = color.g;
      colorArray[index * 3 + 2] = color.b;
    });
    return { positions: positionArray, colors: colorArray };
  }, [segments]);

  useFrame((state, delta) => {
    const group = groupRef.current;
    if (group === null) {
      return;
    }
    if (animate) {
      group.rotation.y += delta * 0.15;
    }
    // Gentle tilt toward the pointer.
    group.rotation.x += (state.pointer.y * 0.3 + 0.35 - group.rotation.x) * 0.05;
    group.rotation.z += (state.pointer.x * -0.2 - group.rotation.z) * 0.05;
  });

  return (
    <group ref={groupRef}>
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[positions, 3]} />
          <bufferAttribute attach="attributes-color" args={[colors, 3]} />
        </bufferGeometry>
        <pointsMaterial
          size={0.09}
          vertexColors
          transparent
          opacity={0.95}
          blending={AdditiveBlending}
          depthWrite={false}
          sizeAttenuation
        />
      </points>
    </group>
  );
}

interface ClaimsOrbProps {
  segments: OrbSegment[];
}

/** 3D view of the claim mix: an AI core with claims orbiting it, coloured by status. */
export default function ClaimsOrb({ segments }: ClaimsOrbProps) {
  const animate = useMemo(
    () =>
      typeof window === "undefined" ||
      !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    [],
  );

  return (
    <Canvas
      camera={{ position: [0, 0.6, 4.6], fov: 45 }}
      dpr={[1, 2]}
      gl={{ antialias: true, alpha: true }}
      aria-hidden="true"
    >
      <Core animate={animate} />
      <OrbitDots segments={segments} animate={animate} />
    </Canvas>
  );
}