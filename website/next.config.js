/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  env: {
    METRICS_BUCKET_BASE: process.env.METRICS_BUCKET_BASE,
  }
}

module.exports = nextConfig
