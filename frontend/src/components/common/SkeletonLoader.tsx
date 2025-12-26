/**
 * SkeletonLoader - Loading placeholder component
 * Maxwell-styled skeleton for loading states
 */

interface SkeletonLoaderProps {
  count?: number;
  className?: string;
  variant?: 'text' | 'circle' | 'rectangle';
}

export default function SkeletonLoader({
  count = 1,
  className = '',
  variant = 'text'
}: SkeletonLoaderProps) {
  const baseClasses = 'animate-pulse bg-slate-ui/30';

  const variantClasses = {
    text: 'h-4 rounded',
    circle: 'rounded-full',
    rectangle: 'rounded-sm',
  };

  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={`${baseClasses} ${variantClasses[variant]} ${className}`}
        />
      ))}
    </>
  );
}

/**
 * ChapterSkeletonItem - Skeleton for chapter list items
 */
export function ChapterSkeletonItem({ level = 0 }: { level?: number }) {
  return (
    <div
      className="flex items-center gap-2 px-3 py-2"
      style={{ paddingLeft: `${level * 1.5 + 0.75}rem` }}
    >
      {/* Icon placeholder */}
      <SkeletonLoader variant="rectangle" className="w-4 h-4 flex-shrink-0" />

      {/* Title placeholder */}
      <SkeletonLoader className="flex-1 h-4" />

      {/* Word count placeholder */}
      <SkeletonLoader variant="rectangle" className="w-12 h-5" />
    </div>
  );
}

/**
 * ChapterTreeSkeleton - Full chapter tree loading state
 */
export function ChapterTreeSkeleton() {
  return (
    <div className="space-y-1 p-2">
      <ChapterSkeletonItem level={0} />
      <ChapterSkeletonItem level={1} />
      <ChapterSkeletonItem level={1} />
      <ChapterSkeletonItem level={0} />
      <ChapterSkeletonItem level={1} />
      <ChapterSkeletonItem level={2} />
      <ChapterSkeletonItem level={1} />
      <ChapterSkeletonItem level={0} />
    </div>
  );
}
