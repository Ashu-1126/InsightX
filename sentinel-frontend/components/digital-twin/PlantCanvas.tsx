"use client";
import { useEffect, useRef } from "react";
import * as THREE from "three";
import type { ZoneRiskScore } from "@/lib/types";

const ZONES_3D = [
  { id: "zone_a", label: "Production\nFloor",  x: -6, z: -3, w: 4, d: 3, h: 1.5 },
  { id: "zone_b", label: "Storage\nArea",      x:  0, z: -3, w: 3, d: 3, h: 2.0 },
  { id: "zone_c", label: "Chemical\nProcess",  x:  5, z: -3, w: 3.5,d: 3, h: 2.5 },
  { id: "zone_d", label: "Loading\nBay",       x: -6, z:  2, w: 3.5,d: 2.5,h: 1.2 },
  { id: "zone_e", label: "Control\nRoom",      x:  0, z:  2, w: 3,  d: 2.5,h: 1.0 },
  { id: "zone_f", label: "Confined\nSpace",    x:  5, z:  2, w: 3,  d: 2.5,h: 3.0 },
];

function riskColor(severity: string): THREE.Color {
  return new THREE.Color(
    severity === "critical" ? 0xef4444 :
    severity === "high"     ? 0xf97316 :
    severity === "medium"   ? 0xf59e0b :
    severity === "warning"  ? 0xf59e0b : 0x10b981
  );
}

interface PlantCanvasProps { zoneScores: ZoneRiskScore[] }

export default function PlantCanvas({ zoneScores }: PlantCanvasProps) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0f);
    scene.fog = new THREE.FogExp2(0x0a0a0f, 0.04);

    // Camera
    const camera = new THREE.PerspectiveCamera(55, container.clientWidth / container.clientHeight, 0.1, 200);
    camera.position.set(0, 14, 14);
    camera.lookAt(0, 0, 0);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    // Lights
    const ambient = new THREE.AmbientLight(0x1a1a2e, 2);
    scene.add(ambient);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(10, 20, 10);
    dirLight.castShadow = true;
    scene.add(dirLight);

    // Grid floor
    const gridHelper = new THREE.GridHelper(30, 30, 0x2a2a3e, 0x1a1a2e);
    scene.add(gridHelper);

    // Floor plane
    const floorGeo = new THREE.PlaneGeometry(30, 20);
    const floorMat = new THREE.MeshLambertMaterial({ color: 0x111118, transparent: true, opacity: 0.8 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    scene.add(floor);

    // Zone score lookup
    const scoreMap: Record<string, ZoneRiskScore> = {};
    for (const z of zoneScores) scoreMap[z.zone_id] = z;

    // Zone meshes
    const zoneMeshes: { mesh: THREE.Mesh; edgeMesh: THREE.LineSegments; zone: typeof ZONES_3D[0]; glowLight: THREE.PointLight }[] = [];

    for (const zone of ZONES_3D) {
      const score = scoreMap[zone.id];
      const severity = score?.severity || "safe";
      const col = riskColor(severity);

      // Main box
      const geo = new THREE.BoxGeometry(zone.w, zone.h, zone.d);
      const mat = new THREE.MeshLambertMaterial({
        color: col,
        transparent: true,
        opacity: severity === "critical" ? 0.55 : severity === "high" ? 0.45 : 0.30,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(zone.x, zone.h / 2, zone.z);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      scene.add(mesh);

      // Wireframe edges
      const edgeGeo = new THREE.EdgesGeometry(geo);
      const edgeMat = new THREE.LineBasicMaterial({ color: col, transparent: true, opacity: 0.7 });
      const edgeMesh = new THREE.LineSegments(edgeGeo, edgeMat);
      edgeMesh.position.copy(mesh.position);
      scene.add(edgeMesh);

      // Glow point light for critical/high zones
      const glowLight = new THREE.PointLight(col.getHex(), severity === "critical" ? 2 : severity === "high" ? 1 : 0, 6);
      glowLight.position.set(zone.x, zone.h + 1, zone.z);
      scene.add(glowLight);

      // Zone label sprite
      const canvas2d = document.createElement("canvas");
      canvas2d.width = 256; canvas2d.height = 128;
      const ctx = canvas2d.getContext("2d")!;
      ctx.clearRect(0, 0, 256, 128);
      ctx.font = "bold 22px 'IBM Plex Mono', monospace";
      ctx.fillStyle = severity === "critical" ? "#ef4444" : severity === "high" ? "#f97316" : "#94a3b8";
      ctx.textAlign = "center";
      const lines = zone.label.split("\n");
      lines.forEach((line, i) => ctx.fillText(line, 128, 36 + i * 28));
      ctx.font = "16px monospace";
      ctx.fillStyle = "#e2e8f0";
      ctx.fillText(score ? `${score.risk_score}` : "0", 128, 96);

      const tex = new THREE.CanvasTexture(canvas2d);
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
      sprite.position.set(zone.x, zone.h + 1.8, zone.z);
      sprite.scale.set(3, 1.5, 1);
      scene.add(sprite);

      zoneMeshes.push({ mesh, edgeMesh, zone, glowLight });
    }

    // Pipe connectors between adjacent zones (decorative)
    const pipePositions = [
      [-6, -3, 0, -3], [0, -3, 5, -3],
      [-6, 2, 0, 2], [0, 2, 5, 2],
      [-6, -0.75, -6, 2], [0, -0.75, 0, 2], [5, -0.75, 5, 2],
    ];
    for (const [x1, z1, x2, z2] of pipePositions) {
      const points = [new THREE.Vector3(x1, 0.1, z1), new THREE.Vector3(x2, 0.1, z2)];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({ color: 0x2a2a3e, transparent: true, opacity: 0.6 });
      scene.add(new THREE.Line(lineGeo, lineMat));
    }

    // Camera rotation (gentle orbit)
    let angle = 0;
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      angle += 0.003;
      camera.position.x = Math.sin(angle) * 16;
      camera.position.z = Math.cos(angle) * 16;
      camera.lookAt(0, 0, 0);

      // Pulse critical zone lights
      const t = performance.now() / 1000;
      for (const { zone, glowLight, mesh, edgeMesh } of zoneMeshes) {
        const score = scoreMap[zone.id];
        const severity = score?.severity || "safe";
        if (severity === "critical") {
          const pulse = 0.5 + 0.5 * Math.sin(t * 4);
          glowLight.intensity = 1.5 + pulse * 2;
          (mesh.material as THREE.MeshLambertMaterial).opacity = 0.4 + pulse * 0.25;
          (edgeMesh.material as THREE.LineBasicMaterial).opacity = 0.5 + pulse * 0.5;
        }
      }

      renderer.render(scene, camera);
    };
    animate();

    // Resize
    const onResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      container.removeChild(renderer.domElement);
    };
  }, [zoneScores]);

  return <div ref={mountRef} className="w-full h-full" />;
}
