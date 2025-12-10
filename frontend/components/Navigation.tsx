'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navigation() {
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: 'Home' },
    { href: '/players', label: 'Players' },
    { href: '/teams', label: 'Teams' },
    { href: '/machines', label: 'Machines' },
    { href: '/venues', label: 'Venues' },
    { href: '/matchups', label: 'Matchups' },
  ];

  return (
    <nav className="shadow-lg" style={{ backgroundColor: '#111827', color: '#ffffff' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link href="/" className="flex items-center">
              <span className="text-xl font-bold" style={{ color: '#ffffff' }}>MNP Analyzer</span>
            </Link>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                    style={{
                      borderColor: isActive ? '#3b82f6' : 'transparent',
                      color: isActive ? '#ffffff' : '#d1d5db',
                    }}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
