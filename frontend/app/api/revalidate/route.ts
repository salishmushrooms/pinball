import { revalidatePath } from 'next/cache';
import { NextRequest, NextResponse } from 'next/server';

// Static pages that can be revalidated
const REVALIDATABLE_PATHS = ['/', '/venues', '/teams'];

/**
 * On-demand revalidation endpoint for triggering cache refresh after ETL runs.
 *
 * Usage:
 *   curl -X POST "https://your-site.vercel.app/api/revalidate?secret=YOUR_SECRET"
 *   curl -X POST "https://your-site.vercel.app/api/revalidate?secret=YOUR_SECRET&path=/venues"
 *
 * Query params:
 *   - secret: Required. Must match REVALIDATION_SECRET env var.
 *   - path: Optional. Specific path to revalidate. If omitted, revalidates all static pages.
 */
export async function POST(request: NextRequest) {
  const secret = request.nextUrl.searchParams.get('secret');
  const path = request.nextUrl.searchParams.get('path');

  // Validate secret
  const expectedSecret = process.env.REVALIDATION_SECRET;
  if (!expectedSecret) {
    return NextResponse.json(
      { error: 'REVALIDATION_SECRET not configured' },
      { status: 500 }
    );
  }

  if (secret !== expectedSecret) {
    return NextResponse.json(
      { error: 'Invalid secret' },
      { status: 401 }
    );
  }

  try {
    const revalidatedPaths: string[] = [];

    if (path) {
      // Revalidate specific path
      if (!REVALIDATABLE_PATHS.includes(path)) {
        return NextResponse.json(
          { error: `Invalid path. Allowed paths: ${REVALIDATABLE_PATHS.join(', ')}` },
          { status: 400 }
        );
      }
      revalidatePath(path);
      revalidatedPaths.push(path);
    } else {
      // Revalidate all static pages
      for (const p of REVALIDATABLE_PATHS) {
        revalidatePath(p);
        revalidatedPaths.push(p);
      }
    }

    return NextResponse.json({
      revalidated: true,
      paths: revalidatedPaths,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Revalidation error:', error);
    return NextResponse.json(
      { error: 'Failed to revalidate', details: String(error) },
      { status: 500 }
    );
  }
}

// Also support GET for easier testing (still requires secret)
export async function GET(request: NextRequest) {
  return POST(request);
}
