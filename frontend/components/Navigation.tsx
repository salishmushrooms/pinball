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
    { href: '/scores', label: 'Scores' },
    { href: '/matchups', label: 'Matchups' },
    { href: '/analysis/weekly', label: 'Weekly' },
    { href: '/live', label: 'Live' },
  ];

  return (
    <nav style={{ backgroundColor: '#111827', color: '#ffffff', borderBottom: '1px solid #2a2a2a' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-14">
          <div className="flex">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-lg font-bold" style={{ color: '#ffffff' }}>Monday Night Pinball</span>
            </Link>
            {/* Desktop navigation */}
            <div className="hidden sm:ml-6 sm:flex sm:items-center sm:space-x-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="inline-flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150"
                    style={{
                      backgroundColor: isActive ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                      color: isActive ? '#ffffff' : '#9ca3af',
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                        e.currentTarget.style.color = '#ffffff';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                        e.currentTarget.style.color = '#9ca3af';
                      }
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
      <div
        className="sm:hidden overflow-hidden transition-all duration-200 ease-in-out"
        id="mobile-menu"
        style={{
          maxHeight: mobileMenuOpen ? `${navItems.length * 44 + 20}px` : '0px',
          opacity: mobileMenuOpen ? 1 : 0,
        }}
      >
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
    </nav>
  );
}
