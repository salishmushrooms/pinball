'use client';

import React, { useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  /** Size of the modal (default: md) */
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  /** Whether to show the close button (default: true) */
  showCloseButton?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-[95vw] sm:max-w-[90vw]',
};

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  showCloseButton = true,
  className,
}: ModalProps) {
  // Handle escape key
  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  // Add/remove escape listener and prevent body scroll
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleEscape]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal content */}
      <div
        className={cn(
          'relative w-full rounded-lg shadow-xl',
          'max-h-[90vh] overflow-y-auto',
          sizeClasses[size],
          className
        )}
        style={{ backgroundColor: 'var(--card-bg)' }}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div
            className="sticky top-0 z-10 flex items-center justify-between px-4 py-3 border-b"
            style={{
              backgroundColor: 'var(--card-bg)',
              borderColor: 'var(--border)',
            }}
          >
            {title && (
              <h2
                id="modal-title"
                className="text-lg font-semibold"
                style={{ color: 'var(--text-primary)' }}
              >
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-1 rounded-md transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
                aria-label="Close modal"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  style={{ color: 'var(--text-muted)' }}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}
