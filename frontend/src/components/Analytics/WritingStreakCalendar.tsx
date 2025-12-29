/**
 * WritingStreakCalendar - GitHub-style contribution heatmap for writing activity
 * Shows daily writing activity over the past weeks/months
 */

import { useMemo } from 'react';

interface WritingStreakCalendarProps {
  dailyStats: Array<{
    date: string;
    word_count: number;
    sessions: number;
  }>;
  days?: number;
}

export default function WritingStreakCalendar({ dailyStats, days = 90 }: WritingStreakCalendarProps) {
  const heatmapData = useMemo(() => {
    // Create a map of dates to data
    const dataMap = new Map(
      dailyStats.map(stat => [stat.date, stat])
    );

    // Generate last N days
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - days);

    const cells = [];
    const currentDate = new Date(startDate);

    while (currentDate <= today) {
      const dateKey = currentDate.toISOString().split('T')[0];
      const data = dataMap.get(dateKey);

      cells.push({
        date: dateKey,
        wordCount: data?.word_count || 0,
        sessions: data?.sessions || 0,
        day: currentDate.getDay(),
      });

      currentDate.setDate(currentDate.getDate() + 1);
    }

    return cells;
  }, [dailyStats, days]);

  // Calculate intensity (0-4) based on word count
  const getIntensity = (wordCount: number): number => {
    if (wordCount === 0) return 0;
    if (wordCount < 250) return 1;
    if (wordCount < 500) return 2;
    if (wordCount < 1000) return 3;
    return 4;
  };

  // Get color class based on intensity
  const getColorClass = (intensity: number): string => {
    const colors = [
      'bg-slate-ui/20',           // 0 - No activity
      'bg-bronze/20',              // 1 - Light activity
      'bg-bronze/40',              // 2 - Moderate activity
      'bg-bronze/60',              // 3 - Good activity
      'bg-bronze',                 // 4 - High activity
    ];
    return colors[intensity];
  };

  // Organize cells into weeks
  const weeks = useMemo(() => {
    const weeksArray: typeof heatmapData[] = [];
    let currentWeek: typeof heatmapData = [];

    // Pad the start to align with Sunday
    const firstDay = heatmapData[0]?.day || 0;
    for (let i = 0; i < firstDay; i++) {
      currentWeek.push({
        date: '',
        wordCount: 0,
        sessions: 0,
        day: i,
      });
    }

    heatmapData.forEach((cell) => {
      currentWeek.push(cell);

      if (cell.day === 6 || cell === heatmapData[heatmapData.length - 1]) {
        // End of week (Saturday) or last cell
        weeksArray.push([...currentWeek]);
        currentWeek = [];
      }
    });

    return weeksArray;
  }, [heatmapData]);

  const months = useMemo(() => {
    const monthLabels: { label: string; weekIndex: number }[] = [];
    let currentMonth = '';

    weeks.forEach((week, weekIndex) => {
      const firstCell = week.find(c => c.date);
      if (firstCell) {
        const date = new Date(firstCell.date);
        const monthName = date.toLocaleDateString('en-US', { month: 'short' });

        if (monthName !== currentMonth) {
          currentMonth = monthName;
          monthLabels.push({ label: monthName, weekIndex });
        }
      }
    });

    return monthLabels;
  }, [weeks]);

  return (
    <div className="writing-streak-calendar">
      {/* Month labels */}
      <div className="flex mb-2">
        <div className="w-8"></div> {/* Spacer for day labels */}
        <div className="flex-1 flex" style={{ marginLeft: '2px' }}>
          {months.map((month, index) => (
            <div
              key={index}
              className="text-xs text-faded-ink font-sans"
              style={{ marginLeft: `${month.weekIndex * 14}px` }}
            >
              {month.label}
            </div>
          ))}
        </div>
      </div>

      {/* Heatmap grid */}
      <div className="flex gap-1">
        {/* Day labels */}
        <div className="flex flex-col gap-1 justify-start pt-[2px]">
          {['', 'Mon', '', 'Wed', '', 'Fri', ''].map((label, index) => (
            <div
              key={index}
              className="h-3 flex items-center justify-end pr-1 text-xs text-faded-ink font-sans"
            >
              {label}
            </div>
          ))}
        </div>

        {/* Weeks */}
        <div className="flex gap-1">
          {weeks.map((week, weekIndex) => (
            <div key={weekIndex} className="flex flex-col gap-1">
              {week.map((cell, cellIndex) => {
                if (!cell.date) {
                  return <div key={cellIndex} className="w-3 h-3"></div>;
                }

                const intensity = getIntensity(cell.wordCount);
                const colorClass = getColorClass(intensity);

                return (
                  <div
                    key={cellIndex}
                    className={`w-3 h-3 ${colorClass} border border-slate-ui/30 rounded-sm cursor-pointer hover:ring-2 hover:ring-bronze transition-all group relative`}
                    title={`${cell.date}: ${cell.wordCount} words, ${cell.sessions} sessions`}
                  >
                    {/* Tooltip on hover */}
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-midnight text-white text-xs rounded-sm opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10 shadow-lg">
                      <div className="font-semibold">{new Date(cell.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</div>
                      <div className="text-slate-ui">{cell.wordCount.toLocaleString()} words</div>
                      <div className="text-slate-ui">{cell.sessions} {cell.sessions === 1 ? 'session' : 'sessions'}</div>
                      {/* Arrow */}
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-midnight"></div>
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-2 mt-4 text-xs text-faded-ink font-sans">
        <span>Less</span>
        <div className="flex gap-1">
          {[0, 1, 2, 3, 4].map((intensity) => (
            <div
              key={intensity}
              className={`w-3 h-3 ${getColorClass(intensity)} border border-slate-ui/30 rounded-sm`}
            ></div>
          ))}
        </div>
        <span>More</span>
      </div>
    </div>
  );
}
