import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required when loading the dev server through Cloudflare Tunnel / similar proxies.
  allowedDevOrigins: ["*.trycloudflare.com"],
};

export default nextConfig;
