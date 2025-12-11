'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

export default function Navigation() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
            {/* Desktop navigation */}
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
          {/* Mobile hamburger button */}
          <div className="flex items-center sm:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md"
              style={{ color: '#d1d5db' }}
              aria-controls="mobile-menu"
              aria-expanded={mobileMenuOpen}
            >
              <span className="sr-only">Open main menu</span>
              {mobileMenuOpen ? (
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className="sm:hidden" id="mobile-menu">
          <div className="pt-2 pb-3 space-y-1" style={{ backgroundColor: '#1f2937' }}>
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
                  style={{
                    borderColor: isActive ? '#3b82f6' : 'transparent',
                    backgroundColor: isActive ? '#374151' : 'transparent',
                    color: isActive ? '#ffffff' : '#d1d5db',
                  }}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </nav>
  );
}
