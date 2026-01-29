/**
 * TitlePageForm - Form editor for title page documents
 * Fields for title, subtitle, author info, synopsis, dedication, and epigraph
 */

import { useState, useEffect, useCallback } from 'react';
import { chaptersApi, type Chapter } from '@/lib/api';
import { toast } from '@/stores/toastStore';
import { getErrorMessage } from '@/lib/retry';

interface TitlePageFormProps {
  chapterId: string;
  onTitleChange?: (title: string) => void;
}

interface TitlePageData {
  bookTitle: string;
  subtitle: string;
  authorName: string;
  authorBio: string;
  synopsis: string;
  dedication: string;
  epigraph: string;
  epigraphAttribution: string;
}

export default function TitlePageForm({ chapterId, onTitleChange: _onTitleChange }: TitlePageFormProps) {
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Title page data
  const [data, setData] = useState<TitlePageData>({
    bookTitle: '',
    subtitle: '',
    authorName: '',
    authorBio: '',
    synopsis: '',
    dedication: '',
    epigraph: '',
    epigraphAttribution: '',
  });

  // Load chapter data
  useEffect(() => {
    const loadChapter = async () => {
      try {
        setLoading(true);
        const chapterData = await chaptersApi.getChapter(chapterId);
        setChapter(chapterData);

        // Extract data from document_metadata
        const meta = chapterData.document_metadata || {};
        setData({
          bookTitle: (meta.bookTitle as string) || '',
          subtitle: (meta.subtitle as string) || '',
          authorName: (meta.authorName as string) || '',
          authorBio: (meta.authorBio as string) || '',
          synopsis: (meta.synopsis as string) || '',
          dedication: (meta.dedication as string) || '',
          epigraph: (meta.epigraph as string) || '',
          epigraphAttribution: (meta.epigraphAttribution as string) || '',
        });
      } catch (err) {
        toast.error(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    loadChapter();
  }, [chapterId]);

  // Auto-save
  const saveChanges = useCallback(async () => {
    if (!chapter || !hasUnsavedChanges) return;

    try {
      setSaving(true);
      await chaptersApi.updateChapter(chapterId, {
        document_metadata: {
          ...chapter.document_metadata,
          ...data,
        },
      });
      setHasUnsavedChanges(false);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }, [chapter, chapterId, data, hasUnsavedChanges]);

  // Auto-save after 2 seconds of inactivity
  useEffect(() => {
    if (!hasUnsavedChanges) return;

    const timer = setTimeout(() => {
      saveChanges();
    }, 2000);

    return () => clearTimeout(timer);
  }, [hasUnsavedChanges, saveChanges]);

  // Update field
  const updateField = (field: keyof TitlePageData, value: string) => {
    setData((prev) => ({ ...prev, [field]: value }));
    setHasUnsavedChanges(true);
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum">
        <div className="text-faded-ink">Loading title page...</div>
      </div>
    );
  }

  if (!chapter) {
    return (
      <div className="flex-1 flex items-center justify-center bg-vellum">
        <div className="text-red-600">Title page not found</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-vellum overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-ui bg-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">📜</span>
            <div>
              <h1 className="font-garamond text-xl font-semibold text-midnight">Title Page</h1>
              <p className="text-xs text-faded-ink">Book front matter</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {hasUnsavedChanges && (
              <span className="text-xs text-amber-600 font-medium">Unsaved changes</span>
            )}
            {saving && <span className="text-xs text-bronze">Saving...</span>}

            <button
              onClick={saveChanges}
              disabled={saving || !hasUnsavedChanges}
              className="px-3 py-1.5 text-xs font-sans bg-bronze text-white hover:bg-bronze/90 disabled:opacity-50 rounded-sm"
            >
              Save
            </button>
          </div>
        </div>
      </div>

      {/* Form content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto p-8 space-y-8">
          {/* Preview Card */}
          <div className="bg-white border border-slate-ui rounded-lg p-8 text-center shadow-sm">
            <div className="space-y-4">
              {data.bookTitle && (
                <h1 className="font-garamond text-4xl font-bold text-midnight">
                  {data.bookTitle}
                </h1>
              )}
              {data.subtitle && (
                <h2 className="font-garamond text-xl text-faded-ink italic">
                  {data.subtitle}
                </h2>
              )}
              {data.authorName && (
                <p className="text-lg text-midnight mt-8">by {data.authorName}</p>
              )}
            </div>
          </div>

          {/* Form Sections */}
          <FormSection title="Title & Author">
            <FormField
              label="Book Title"
              value={data.bookTitle}
              onChange={(v) => updateField('bookTitle', v)}
              placeholder="Your book title"
            />
            <FormField
              label="Subtitle"
              value={data.subtitle}
              onChange={(v) => updateField('subtitle', v)}
              placeholder="Optional subtitle"
            />
            <FormField
              label="Author Name"
              value={data.authorName}
              onChange={(v) => updateField('authorName', v)}
              placeholder="Your pen name or real name"
            />
            <FormTextarea
              label="Author Bio"
              value={data.authorBio}
              onChange={(v) => updateField('authorBio', v)}
              placeholder="A brief author biography for the back cover or about page..."
              rows={4}
            />
          </FormSection>

          <FormSection title="Synopsis / Blurb">
            <FormTextarea
              label="Book Synopsis"
              value={data.synopsis}
              onChange={(v) => updateField('synopsis', v)}
              placeholder="The back-cover blurb or book description..."
              rows={6}
            />
            <p className="text-xs text-faded-ink mt-1">
              Tip: Keep it intriguing but avoid spoilers. This is what readers will see before buying.
            </p>
          </FormSection>

          <FormSection title="Dedication & Epigraph">
            <FormTextarea
              label="Dedication"
              value={data.dedication}
              onChange={(v) => updateField('dedication', v)}
              placeholder="For my family, who believed in me..."
              rows={3}
            />
            <FormTextarea
              label="Epigraph"
              value={data.epigraph}
              onChange={(v) => updateField('epigraph', v)}
              placeholder="A quote that sets the tone for your book..."
              rows={3}
            />
            <FormField
              label="Epigraph Attribution"
              value={data.epigraphAttribution}
              onChange={(v) => updateField('epigraphAttribution', v)}
              placeholder="— Author Name, Source"
            />
          </FormSection>
        </div>
      </div>
    </div>
  );
}

// Helper Components

interface FormSectionProps {
  title: string;
  children: React.ReactNode;
}

function FormSection({ title, children }: FormSectionProps) {
  return (
    <div className="bg-white rounded-lg border border-slate-ui p-5">
      <h2 className="font-garamond text-lg font-semibold text-midnight mb-4">{title}</h2>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

interface FormFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

function FormField({ label, value, onChange, placeholder }: FormFieldProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-midnight mb-1">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 text-sm border border-slate-ui rounded-sm focus:outline-none focus:ring-2 focus:ring-bronze/50 focus:border-bronze bg-vellum"
      />
    </div>
  );
}

interface FormTextareaProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
}

function FormTextarea({ label, value, onChange, placeholder, rows = 3 }: FormTextareaProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-midnight mb-1">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="w-full px-3 py-2 text-sm border border-slate-ui rounded-sm focus:outline-none focus:ring-2 focus:ring-bronze/50 focus:border-bronze bg-vellum resize-none"
      />
    </div>
  );
}
