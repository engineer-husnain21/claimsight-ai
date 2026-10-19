import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Every page depends on the user's session cookie, so caching gives no benefit here.
  cacheComponents: false,
  // Do not advertise the framework in response headers.
  poweredByHeader: false,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;