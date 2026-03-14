/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    const backend = process.env.BACKEND_URL || 'http://localhost:8000';
    return [
      { source: '/api/proxy/:path*', destination: `${backend}/api/:path*` },
    ];
  },
};

module.exports = nextConfig;
