"use client";

import { useRef } from "react";
import Map, { type MapRef } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";

const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

const GLOBAL_VIEW = {
  longitude: -40,
  latitude: 20,
  zoom: 1,
} as const;

const TARGET_VIEW = {
  longitude: -121.7617,
  latitude: 38.5382,
  zoom: 15.5,
} as const;

const INTRO_DURATION_MS = 3000;
const INTRO_SESSION_KEY = "mapview:introPlayed";

function prefersReducedMotion() {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function MapboxMap() {
  const mapRef = useRef<MapRef>(null);

  if (!token) {
    return (
      <div className="flex h-full min-h-[420px] flex-col items-center justify-center gap-3 bg-neutral-100 p-6 text-center">
        <p className="font-medium text-neutral-800">Mapbox token missing</p>
        <p className="max-w-md text-sm text-neutral-600">
          Create{" "}
          <code className="rounded bg-white px-1.5 py-0.5 text-xs">
            frontend/.env.local
          </code>{" "}
          with:
        </p>
        <pre className="rounded-lg bg-white p-4 text-left text-xs text-neutral-800 shadow-sm">
          {`NEXT_PUBLIC_MAPBOX_TOKEN=pk.your_token_here`}
        </pre>
        <p className="text-xs text-neutral-500">
          Copy the default public token from{" "}
          <span className="text-neutral-700">console.mapbox.com</span> →
          Account → Tokens.
        </p>
      </div>
    );
  }

  return (
    <Map
      ref={mapRef}
      mapboxAccessToken={token}
      initialViewState={GLOBAL_VIEW}
      projection={{ name: "globe" }}
      style={{ width: "100%", height: "100%" }}
      mapStyle="mapbox://styles/mapbox/streets-v12"
      onLoad={() => {
        const map = mapRef.current?.getMap();
        if (!map) return;

        const target = {
          center: [TARGET_VIEW.longitude, TARGET_VIEW.latitude] as [
            number,
            number,
          ],
          zoom: TARGET_VIEW.zoom,
        };

        const alreadyPlayed =
          typeof sessionStorage !== "undefined" &&
          sessionStorage.getItem(INTRO_SESSION_KEY) === "1";

        if (alreadyPlayed || prefersReducedMotion()) {
          map.jumpTo(target);
          return;
        }

        map.flyTo({
          ...target,
          duration: INTRO_DURATION_MS,
          curve: 1.6,
          essential: false,
        });

        try {
          sessionStorage.setItem(INTRO_SESSION_KEY, "1");
        } catch {
          // sessionStorage may be unavailable (e.g., privacy mode); ignore.
        }
      }}
    />
  );
}
