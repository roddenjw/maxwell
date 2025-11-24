/**
 * Lexical Editor Theme Configuration
 * Defines CSS classes for editor elements
 */

import type { EditorTheme } from '@/types/editor';

export const editorTheme: EditorTheme = {
  ltr: 'ltr',
  rtl: 'rtl',
  paragraph: 'editor-paragraph',
  heading: {
    h1: 'editor-heading-h1 text-4xl font-bold mt-8 mb-4',
    h2: 'editor-heading-h2 text-3xl font-bold mt-6 mb-3',
    h3: 'editor-heading-h3 text-2xl font-semibold mt-4 mb-2',
    h4: 'editor-heading-h4 text-xl font-semibold mt-3 mb-2',
    h5: 'editor-heading-h5 text-lg font-semibold mt-2 mb-1',
    h6: 'editor-heading-h6 text-base font-semibold mt-2 mb-1',
  },
  text: {
    bold: 'font-bold',
    italic: 'italic',
    underline: 'underline',
    strikethrough: 'line-through',
    code: 'font-mono bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm',
  },
  list: {
    ul: 'editor-list-ul list-disc list-inside my-4',
    ol: 'editor-list-ol list-decimal list-inside my-4',
    listitem: 'editor-listitem ml-4',
  },
  quote: 'editor-quote border-l-4 border-primary-500 pl-4 italic my-4 text-gray-700 dark:text-gray-300',
  link: 'text-primary-600 dark:text-primary-400 underline hover:text-primary-700 cursor-pointer',
};

export default editorTheme;
