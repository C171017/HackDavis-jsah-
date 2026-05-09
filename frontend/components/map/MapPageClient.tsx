"use client";

import dynamic from "next/dynamic";

const MapboxMap = dynamic(
  () => import("@/components/map/MapboxMap").then((m) => m.MapboxMap),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[100dvh] items-center justify-center bg-neutral-950 text-neutral-400">
        Loading map…
      </div>
    ),
  },
);

export function MapPageClient() {
  return (
    <div className="relative h-[100dvh] w-full overflow-hidden">
      <MapboxMap />
    </div>
  );
}
