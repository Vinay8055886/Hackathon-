/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Reports are rendered client-side from fetched blobs; no remote images.
  images: { unoptimized: true },
};

module.exports = nextConfig;
