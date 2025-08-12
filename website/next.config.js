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
  },
  // Configure build ID for better caching
  generateBuildId: async () => {
    // Use a consistent build ID in development, dynamic in production
    if (process.env.NODE_ENV === 'development') {
      return 'development'
    }
    // Use git commit hash if available, fallback to timestamp
    return process.env.AMPLIFY_COMMIT_ID || 
           process.env.VERCEL_GIT_COMMIT_SHA || 
           `build-${Date.now()}`
  }
}

module.exports = nextConfig
