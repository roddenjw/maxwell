/**
 * TimelineTeachingPanel - Curated teaching moments from timeline validation
 */

import { useTimelineStore } from '@/stores/timelineStore';
import { getSeverityIcon } from '@/types/timeline';

interface TimelineTeachingPanelProps {
  manuscriptId: string;
}

export default function TimelineTeachingPanel({ }: TimelineTeachingPanelProps) {
  const { getFilteredInconsistencies } = useTimelineStore();

  const issuesWithTeaching = getFilteredInconsistencies().filter(
    (issue) => issue.teaching_point && !issue.is_resolved
  );

  // Group by inconsistency type
  const groupedTeachings = issuesWithTeaching.reduce((acc, issue) => {
    const type = issue.inconsistency_type;
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(issue);
    return acc;
  }, {} as Record<string, typeof issuesWithTeaching>);

  if (issuesWithTeaching.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <div className="text-6xl mb-4">📚</div>
        <h3 className="text-xl font-garamond font-bold text-midnight mb-2">
          No Teaching Moments Yet
        </h3>
        <p className="text-sm text-faded-ink font-sans max-w-md">
          Run timeline validation to discover issues and learn about reader psychology and narrative craft.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <h2 className="text-xl font-garamond font-bold text-midnight mb-1">Teaching Moments</h2>
        <p className="text-sm text-faded-ink font-sans">
          Learn about reader psychology and narrative craft from your timeline issues
        </p>
      </div>

      {/* Teaching Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {Object.entries(groupedTeachings).map(([type, issues]) => (
          <div key={type} className="border border-slate-ui bg-white p-4" style={{ borderRadius: '2px' }}>
            {/* Type Header */}
            <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-ui">
              <span className="text-2xl">📖</span>
              <div className="flex-1">
                <h3 className="text-sm font-sans font-semibold text-bronze uppercase">
                  {type.replace(/_/g, ' ')}
                </h3>
                <p className="text-xs text-faded-ink font-sans">
                  {issues.length} occurrence{issues.length > 1 ? 's' : ''} in your timeline
                </p>
              </div>
            </div>

            {/* Teaching Points */}
            <div className="space-y-4">
              {issues.slice(0, 1).map((issue) => (
                <div key={issue.id}>
                  {/* The Issue Example */}
                  <div className="mb-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm">{getSeverityIcon(issue.severity)}</span>
                      <h4 className="text-sm font-sans font-semibold text-midnight">Example from your story:</h4>
                    </div>
                    <p className="text-sm font-serif text-midnight italic pl-6">
                      {issue.description}
                    </p>
                  </div>

                  {/* The Teaching */}
                  {issue.teaching_point && (
                    <div className="bg-bronze/5 p-3 border-l-4 border-bronze">
                      <h4 className="text-sm font-sans font-semibold text-bronze mb-2">
                        📚 Why This Matters
                      </h4>
                      <p className="text-sm font-serif text-midnight whitespace-pre-line leading-relaxed">
                        {issue.teaching_point}
                      </p>
                    </div>
                  )}

                  {/* The Suggestions */}
                  {issue.suggestion && (
                    <div className="mt-3 bg-vellum p-3">
                      <h4 className="text-sm font-sans font-semibold text-midnight mb-2">
                        💡 Ways to Address This
                      </h4>
                      <p className="text-sm font-serif text-midnight whitespace-pre-line">
                        {issue.suggestion}
                      </p>
                    </div>
                  )}
                </div>
              ))}

              {/* More Examples Link */}
              {issues.length > 1 && (
                <div className="pt-2 border-t border-slate-ui">
                  <p className="text-xs text-faded-ink font-sans">
                    + {issues.length - 1} more example{issues.length > 1 ? 's' : ''} in your timeline
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Footer Note */}
        <div className="border border-bronze bg-white p-4" style={{ borderRadius: '2px' }}>
          <div className="flex items-start gap-3">
            <span className="text-2xl">💡</span>
            <div>
              <h4 className="text-sm font-sans font-semibold text-bronze mb-1">
                Remember: These are suggestions, not rules
              </h4>
              <p className="text-sm font-serif text-midnight">
                Every story is unique. These teaching moments explain reader psychology and offer options—
                not prescriptions. Trust your creative instincts and choose what serves your story best.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
