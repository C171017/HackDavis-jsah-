import { useRef } from "react";
import Map, { type MapRef } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";

const token = import.meta.env.VITE_MAPBOX_TOKEN;

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

export function MapView() {
  const mapRef = useRef<MapRef>(null);

  if (!token) {
    return (
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-4 bg-neutral-100 p-8 text-center">
        <p className="font-medium text-neutral-800">Missing Mapbox token</p>
        <p className="max-w-md text-sm text-neutral-600">
          Add{" "}
          <code className="rounded bg-white px-1.5 py-0.5 font-mono text-xs">
            VITE_MAPBOX_TOKEN
          </code>{" "}
          to{" "}
          <code className="rounded bg-white px-1.5 py-0.5 font-mono text-xs">
            frontend/.env.local
          </code>
          :
        </p>
        <pre className="rounded-lg bg-white p-4 text-left font-mono text-xs text-neutral-800 shadow-sm">
          VITE_MAPBOX_TOKEN=pk.your_token_here
        </pre>
        <p className="max-w-sm text-xs text-neutral-500">
          Use the default public token from mapbox.com (starts with{" "}
          <span className="font-mono">pk.</span>).
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
