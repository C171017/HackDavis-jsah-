"use client";

import { useCallback, useRef, useState } from "react";
import type { Map as MapboxGLMap } from "mapbox-gl";
import Map, { type MapRef } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";

/** Mapbox Standard — 3D buildings, dynamic lighting; labels toggled via basemap config. */
const MAP_STYLE = "mapbox://styles/mapbox/standard";

/**
 * Standard style uses an imported `basemap` fragment — configure lighting + labels there
 * (not by hiding symbol layers, which fights the Standard renderer).
 */
function configureStandardBasemap(map: MapboxGLMap) {
  const apply = () => {
    const props = [
      ["lightPreset", "day"],
      ["showPlaceLabels", false],
      ["showPointOfInterestLabels", false],
      ["showRoadLabels", false],
      ["showTransitLabels", false],
    ] as const;
    for (const [key, value] of props) {
      try {
        map.setConfigProperty("basemap", key, value);
      } catch {
        // Property may be absent in older Standard revisions or schema mismatch.
      }
    }
  };

  if (map.isStyleLoaded()) apply();
  else map.once("style.load", apply);
}

const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

/** Globe overview before flying to campus. */
const GLOBAL_VIEW = {
  longitude: -40,
  latitude: 20,
  zoom: 1,
} as const;

/** UC Davis — Memorial Union / campus core (matches prior MapView spec). */
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

function LocateMeIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden
    >
      <path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3A8.994 8.994 0 0 0 13 3.06V1h-2v2.06A8.994 8.994 0 0 0 3.06 11H1v2h2.06A8.994 8.994 0 0 0 11 20.94V23h2v-2.06A8.994 8.994 0 0 0 20.94 13H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z" />
    </svg>
  );
}

export function MapboxMap() {
  const mapRef = useRef<MapRef>(null);
  const [locating, setLocating] = useState(false);
  const [geoHint, setGeoHint] = useState<string | null>(null);

  const goToMyLocation = useCallback(() => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGeoHint("Geolocation is not supported in this browser.");
      return;
    }

    setGeoHint(null);
    setLocating(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const map = mapRef.current?.getMap();
        if (!map) {
          setLocating(false);
          return;
        }
        const { longitude, latitude } = position.coords;
        map.flyTo({
          center: [longitude, latitude],
          zoom: Math.max(map.getZoom(), 14),
          duration: 1500,
          essential: true,
        });
        setLocating(false);
      },
      (err) => {
        setLocating(false);
        const msg =
          err.code === err.PERMISSION_DENIED
            ? "Location permission was denied."
            : err.message || "Could not get your location.";
        setGeoHint(msg);
      },
      { enableHighAccuracy: true, timeout: 12_000, maximumAge: 0 },
    );
  }, []);

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
    <div className="relative h-full w-full">
      <Map
        ref={mapRef}
        mapboxAccessToken={token}
        initialViewState={GLOBAL_VIEW}
        projection={{ name: "globe" }}
        style={{ width: "100%", height: "100%" }}
        mapStyle={MAP_STYLE}
        onLoad={() => {
          const map = mapRef.current?.getMap();
          if (!map) return;

          configureStandardBasemap(map);

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
      <button
        type="button"
        onClick={goToMyLocation}
        disabled={locating}
        className="absolute bottom-4 right-4 z-10 flex h-11 w-11 items-center justify-center rounded-lg border border-neutral-200 bg-white text-neutral-700 shadow-md transition hover:bg-neutral-50 disabled:cursor-wait disabled:opacity-70"
        aria-label="Go to my location"
        title={geoHint ?? "Go to my location"}
      >
        <LocateMeIcon className="h-6 w-6" />
      </button>
    </div>
  );
}
