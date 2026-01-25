/**
 * ViewLoadingSpinner - Loading spinner for lazy-loaded views
 * Matches Maxwell design system (vellum bg, bronze spinner)
 */

export default function ViewLoadingSpinner() {
  return (
    <div className="flex-1 flex items-center justify-center bg-vellum">
      <div className="text-center">
        {/* Spinner */}
        <div className="relative w-12 h-12 mx-auto mb-4">
          <div className="absolute inset-0 border-4 border-bronze/20 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-transparent border-t-bronze rounded-full animate-spin"></div>
        </div>
        {/* Loading text */}
        <p className="text-faded-ink font-sans text-sm">Loading...</p>
      </div>
    </div>
  );
}
