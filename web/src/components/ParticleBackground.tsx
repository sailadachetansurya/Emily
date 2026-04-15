"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";

// Generate random particles in a sphere
function generateParticles(count: number) {
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const r = 2 + Math.random() * 3; // Radius between 2-5
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);

    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    positions[i * 3 + 2] = r * Math.cos(phi);
  }
  return positions;
}

function ParticleField({ count = 500 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null);

  const positions = useMemo(() => generateParticles(count), [count]);

  useFrame((state, delta) => {
    if (ref.current) {
      ref.current.rotation.x -= delta * 0.05;
      ref.current.rotation.y -= delta * 0.03;
    }
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#8B5CF6"
        size={0.05}
        sizeAttenuation={true}
        depthWrite={false}
        opacity={0.6}
      />
    </Points>
  );
}

function GlowOrbs() {
  const orb1Ref = useRef<THREE.Mesh>(null);
  const orb2Ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime * 0.5;

    if (orb1Ref.current) {
      orb1Ref.current.position.x = Math.sin(t) * 2;
      orb1Ref.current.position.y = Math.cos(t * 0.7) * 2;
      orb1Ref.current.position.z = Math.sin(t * 0.5) * 1 - 3;
      orb1Ref.current.scale.setScalar(1 + Math.sin(t * 2) * 0.2);
    }

    if (orb2Ref.current) {
      orb2Ref.current.position.x = Math.cos(t * 0.8) * 2.5;
      orb2Ref.current.position.y = Math.sin(t * 0.6) * 2.5;
      orb2Ref.current.position.z = Math.cos(t * 0.4) * 1 - 3;
      orb2Ref.current.scale.setScalar(1 + Math.cos(t * 1.5) * 0.2);
    }
  });

  return (
    <>
      <mesh ref={orb1Ref}>
        <sphereGeometry args={[0.3, 32, 32]} />
        <meshBasicMaterial color="#A3E635" transparent opacity={0.3} />
      </mesh>
      <mesh ref={orb2Ref}>
        <sphereGeometry args={[0.4, 32, 32]} />
        <meshBasicMaterial color="#F97316" transparent opacity={0.25} />
      </mesh>
    </>
  );
}

export default function ParticleBackground() {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 60 }}
      style={{ background: "transparent" }}
    >
      <ambientLight intensity={0.5} />
      <ParticleField count={600} />
      <GlowOrbs />
    </Canvas>
  );
}
