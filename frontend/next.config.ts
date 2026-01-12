import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'imagedelivery.net',
        port: '',
        pathname: '/6xApIkGdPK3UoS1ME8gCmA/**',
      },
    ],
  },
};

export default nextConfig;
