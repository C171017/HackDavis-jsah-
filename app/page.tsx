import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-2xl font-semibold tracking-tight">Food Pantry</h1>
      <p className="max-w-md text-center text-neutral-600">
        Map uses Mapbox. Add your token to{" "}
        <code className="rounded bg-neutral-100 px-1.5 py-0.5 text-sm">
          .env.local
        </code>{" "}
        (see below).
      </p>
      <Link
        href="/map"
        className="rounded-lg bg-neutral-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-neutral-800"
      >
        Open map
      </Link>
    </main>
  );
}
