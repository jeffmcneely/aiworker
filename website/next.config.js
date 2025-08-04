/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://api.mcneely.io/v1/ai/:path*',
      },
    ]
  },
}

module.exports = nextConfig
