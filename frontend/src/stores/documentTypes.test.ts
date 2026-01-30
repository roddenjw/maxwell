/**
 * Tests for Document Types (Scrivener-style documents)
 *
 * This test suite covers:
 * 1. Document type constants and types
 * 2. Chapter store handling of different document types
 * 3. Document metadata storage
 * 4. Linked entity handling
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import { useChapterStore } from './chapterStore';
import type { Chapter, ChapterTree, DocumentType } from '@/lib/api';

describe('Document Types', () => {
  // Reset store before each test
  beforeEach(() => {
    useChapterStore.setState({
      chapters: [],
      chapterTree: [],
      currentChapterId: null,
      expandedFolders: new Set(),
    });
  });

  // Sample chapters for testing
  const createChapter = (overrides: Partial<Chapter> = {}): Chapter => ({
    id: `chapter-${Math.random().toString(36).substring(7)}`,
    manuscript_id: 'ms-1',
    parent_id: null,
    title: 'Test Chapter',
    is_folder: false,
    order_index: 0,
    lexical_state: '',
    content: '',
    word_count: 0,
    document_type: 'CHAPTER',
    linked_entity_id: null,
    document_metadata: {},
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    ...overrides,
  });

  describe('Document Type Constants', () => {
    it('should recognize CHAPTER document type', () => {
      const chapter = createChapter({ document_type: 'CHAPTER' });
      expect(chapter.document_type).toBe('CHAPTER');
    });

    it('should recognize FOLDER document type', () => {
      const folder = createChapter({
        document_type: 'FOLDER',
        is_folder: true,
        title: 'Folder',
      });
      expect(folder.document_type).toBe('FOLDER');
      expect(folder.is_folder).toBe(true);
    });

    it('should recognize CHARACTER_SHEET document type', () => {
      const sheet = createChapter({
        document_type: 'CHARACTER_SHEET',
        title: 'Hero - Character Sheet',
        document_metadata: { name: 'Hero', role: 'Protagonist' },
      });
      expect(sheet.document_type).toBe('CHARACTER_SHEET');
      expect(sheet.document_metadata?.name).toBe('Hero');
    });

    it('should recognize NOTES document type', () => {
      const notes = createChapter({
        document_type: 'NOTES',
        title: 'Research Notes',
        document_metadata: { tags: ['worldbuilding'], category: 'Research' },
      });
      expect(notes.document_type).toBe('NOTES');
      expect(notes.document_metadata?.category).toBe('Research');
    });

    it('should recognize TITLE_PAGE document type', () => {
      const titlePage = createChapter({
        document_type: 'TITLE_PAGE',
        title: 'Title Page',
        document_metadata: {
          title: 'The Epic Novel',
          author: 'Jane Writer',
          synopsis: 'An epic tale...',
        },
      });
      expect(titlePage.document_type).toBe('TITLE_PAGE');
      expect(titlePage.document_metadata?.author).toBe('Jane Writer');
    });
  });

  describe('Chapter Store with Document Types', () => {
    it('should add chapters with different document types', () => {
      const chapter = createChapter({ document_type: 'CHAPTER', id: 'ch-1' });
      const notes = createChapter({ document_type: 'NOTES', id: 'notes-1' });
      const sheet = createChapter({ document_type: 'CHARACTER_SHEET', id: 'sheet-1' });

      act(() => {
        useChapterStore.getState().addChapter(chapter);
        useChapterStore.getState().addChapter(notes);
        useChapterStore.getState().addChapter(sheet);
      });

      const { chapters } = useChapterStore.getState();
      expect(chapters).toHaveLength(3);

      const docTypes = chapters.map(ch => ch.document_type);
      expect(docTypes).toContain('CHAPTER');
      expect(docTypes).toContain('NOTES');
      expect(docTypes).toContain('CHARACTER_SHEET');
    });

    it('should update document_metadata', () => {
      const sheet = createChapter({
        id: 'sheet-1',
        document_type: 'CHARACTER_SHEET',
        document_metadata: { name: 'Original Name' },
      });

      act(() => {
        useChapterStore.getState().addChapter(sheet);
        useChapterStore.getState().updateChapter('sheet-1', {
          document_metadata: {
            name: 'Updated Name',
            aliases: ['New Alias'],
            role: 'Antagonist',
          },
        });
      });

      const { chapters } = useChapterStore.getState();
      const updated = chapters.find(ch => ch.id === 'sheet-1');
      expect(updated?.document_metadata?.name).toBe('Updated Name');
      expect(updated?.document_metadata?.role).toBe('Antagonist');
    });

    it('should handle linked_entity_id', () => {
      const sheet = createChapter({
        id: 'sheet-1',
        document_type: 'CHARACTER_SHEET',
        linked_entity_id: 'entity-123',
      });

      act(() => {
        useChapterStore.getState().addChapter(sheet);
      });

      const { chapters } = useChapterStore.getState();
      const linkedSheet = chapters.find(ch => ch.id === 'sheet-1');
      expect(linkedSheet?.linked_entity_id).toBe('entity-123');
    });

    it('should allow unlinking entity', () => {
      const sheet = createChapter({
        id: 'sheet-1',
        document_type: 'CHARACTER_SHEET',
        linked_entity_id: 'entity-123',
      });

      act(() => {
        useChapterStore.getState().addChapter(sheet);
        useChapterStore.getState().updateChapter('sheet-1', {
          linked_entity_id: null,
        });
      });

      const { chapters } = useChapterStore.getState();
      const unlinkedSheet = chapters.find(ch => ch.id === 'sheet-1');
      expect(unlinkedSheet?.linked_entity_id).toBeNull();
    });
  });

  describe('Character Sheet Metadata', () => {
    it('should store all character sheet sections', () => {
      const metadata = {
        name: 'Aria',
        aliases: ['The Shadow', 'Lady A'],
        role: 'Protagonist',
        physical: {
          age: '28',
          appearance: 'Tall with dark hair',
          distinguishing_features: 'Scar on left cheek',
        },
        personality: {
          traits: ['Brave', 'Stubborn', 'Loyal'],
          strengths: 'Strategic thinking',
          flaws: 'Too trusting',
        },
        backstory: {
          origin: 'Born in a small village',
          key_events: 'Lost family in the war',
          secrets: 'Has a hidden twin',
        },
        motivation: {
          want: 'Revenge against the empire',
          need: 'To learn forgiveness',
        },
        notes: 'Important character arc in Act 2',
      };

      const sheet = createChapter({
        id: 'sheet-1',
        document_type: 'CHARACTER_SHEET',
        document_metadata: metadata,
      });

      act(() => {
        useChapterStore.getState().addChapter(sheet);
      });

      const { chapters } = useChapterStore.getState();
      const stored = chapters.find(ch => ch.id === 'sheet-1');

      expect(stored?.document_metadata?.name).toBe('Aria');
      expect(stored?.document_metadata?.role).toBe('Protagonist');
      expect((stored?.document_metadata?.physical as any)?.age).toBe('28');
      expect((stored?.document_metadata?.personality as any)?.traits).toContain('Brave');
      expect((stored?.document_metadata?.backstory as any)?.secrets).toBe('Has a hidden twin');
      expect((stored?.document_metadata?.motivation as any)?.want).toBe('Revenge against the empire');
    });
  });

  describe('Notes Metadata', () => {
    it('should store tags and category', () => {
      const notes = createChapter({
        id: 'notes-1',
        document_type: 'NOTES',
        content: 'Research notes about magic system',
        document_metadata: {
          tags: ['worldbuilding', 'magic', 'rules'],
          category: 'Research',
        },
      });

      act(() => {
        useChapterStore.getState().addChapter(notes);
      });

      const { chapters } = useChapterStore.getState();
      const stored = chapters.find(ch => ch.id === 'notes-1');

      expect(stored?.document_metadata?.tags).toHaveLength(3);
      expect((stored?.document_metadata?.tags as string[])).toContain('magic');
      expect(stored?.document_metadata?.category).toBe('Research');
    });

    it('should update tags', () => {
      const notes = createChapter({
        id: 'notes-1',
        document_type: 'NOTES',
        document_metadata: { tags: ['initial'] },
      });

      act(() => {
        useChapterStore.getState().addChapter(notes);
        useChapterStore.getState().updateChapter('notes-1', {
          document_metadata: {
            tags: ['updated', 'new-tag'],
          },
        });
      });

      const { chapters } = useChapterStore.getState();
      const stored = chapters.find(ch => ch.id === 'notes-1');
      expect((stored?.document_metadata?.tags as string[])).toContain('updated');
      expect((stored?.document_metadata?.tags as string[])).not.toContain('initial');
    });
  });

  describe('Title Page Metadata', () => {
    it('should store all title page fields', () => {
      const titlePage = createChapter({
        id: 'title-1',
        document_type: 'TITLE_PAGE',
        document_metadata: {
          title: 'The Great Adventure',
          subtitle: 'A Tale of Heroes',
          author: 'John Author',
          author_bio: 'John is an award-winning writer.',
          synopsis: 'In a world where magic is forbidden...',
          dedication: 'To my family',
          epigraph: 'All that glitters is not gold.',
          epigraph_attribution: 'William Shakespeare',
        },
      });

      act(() => {
        useChapterStore.getState().addChapter(titlePage);
      });

      const { chapters } = useChapterStore.getState();
      const stored = chapters.find(ch => ch.id === 'title-1');

      expect(stored?.document_metadata?.title).toBe('The Great Adventure');
      expect(stored?.document_metadata?.author).toBe('John Author');
      expect(stored?.document_metadata?.synopsis).toContain('magic is forbidden');
      expect(stored?.document_metadata?.epigraph_attribution).toBe('William Shakespeare');
    });
  });

  describe('Folder with Mixed Document Types', () => {
    it('should support nested documents of different types', () => {
      const folder = createChapter({
        id: 'folder-1',
        document_type: 'FOLDER',
        is_folder: true,
        title: 'Characters',
      });

      const sheet1 = createChapter({
        id: 'sheet-1',
        document_type: 'CHARACTER_SHEET',
        parent_id: 'folder-1',
        title: 'Hero',
      });

      const sheet2 = createChapter({
        id: 'sheet-2',
        document_type: 'CHARACTER_SHEET',
        parent_id: 'folder-1',
        title: 'Villain',
      });

      const notes = createChapter({
        id: 'notes-1',
        document_type: 'NOTES',
        parent_id: 'folder-1',
        title: 'Character Ideas',
      });

      act(() => {
        useChapterStore.getState().addChapter(folder);
        useChapterStore.getState().addChapter(sheet1);
        useChapterStore.getState().addChapter(sheet2);
        useChapterStore.getState().addChapter(notes);
      });

      const { chapters } = useChapterStore.getState();
      const children = chapters.filter(ch => ch.parent_id === 'folder-1');

      expect(children).toHaveLength(3);
      expect(children.filter(ch => ch.document_type === 'CHARACTER_SHEET')).toHaveLength(2);
      expect(children.filter(ch => ch.document_type === 'NOTES')).toHaveLength(1);
    });
  });

  describe('ChapterTree with Document Types', () => {
    it('should include document_type and linked_entity_id in tree', () => {
      const tree: ChapterTree[] = [
        {
          id: 'folder-1',
          title: 'Characters',
          is_folder: true,
          order_index: 0,
          word_count: 0,
          document_type: 'FOLDER',
          linked_entity_id: null,
          children: [
            {
              id: 'sheet-1',
              title: 'Hero',
              is_folder: false,
              order_index: 0,
              word_count: 0,
              document_type: 'CHARACTER_SHEET',
              linked_entity_id: 'entity-123',
              children: [],
            },
          ],
        },
        {
          id: 'chapter-1',
          title: 'Chapter 1',
          is_folder: false,
          order_index: 1,
          word_count: 500,
          document_type: 'CHAPTER',
          linked_entity_id: null,
          children: [],
        },
      ];

      act(() => {
        useChapterStore.getState().setChapterTree(tree);
      });

      const { chapterTree } = useChapterStore.getState();
      expect(chapterTree[0].document_type).toBe('FOLDER');
      expect(chapterTree[0].children[0].document_type).toBe('CHARACTER_SHEET');
      expect(chapterTree[0].children[0].linked_entity_id).toBe('entity-123');
      expect(chapterTree[1].document_type).toBe('CHAPTER');
    });
  });

  describe('Document Type Helpers', () => {
    it('should identify linked character sheets', () => {
      const linkedSheet = createChapter({
        id: 'sheet-1',
        document_type: 'CHARACTER_SHEET',
        linked_entity_id: 'entity-123',
      });

      const unlinkedSheet = createChapter({
        id: 'sheet-2',
        document_type: 'CHARACTER_SHEET',
        linked_entity_id: null,
      });

      act(() => {
        useChapterStore.getState().addChapter(linkedSheet);
        useChapterStore.getState().addChapter(unlinkedSheet);
      });

      const { chapters } = useChapterStore.getState();
      const linked = chapters.filter(ch =>
        ch.document_type === 'CHARACTER_SHEET' && ch.linked_entity_id
      );
      const unlinked = chapters.filter(ch =>
        ch.document_type === 'CHARACTER_SHEET' && !ch.linked_entity_id
      );

      expect(linked).toHaveLength(1);
      expect(unlinked).toHaveLength(1);
    });

    it('should filter by document type', () => {
      act(() => {
        useChapterStore.getState().addChapter(createChapter({ id: 'ch-1', document_type: 'CHAPTER' }));
        useChapterStore.getState().addChapter(createChapter({ id: 'ch-2', document_type: 'CHAPTER' }));
        useChapterStore.getState().addChapter(createChapter({ id: 'notes-1', document_type: 'NOTES' }));
        useChapterStore.getState().addChapter(createChapter({ id: 'sheet-1', document_type: 'CHARACTER_SHEET' }));
      });

      const { chapters } = useChapterStore.getState();

      const chapterDocs = chapters.filter(ch => ch.document_type === 'CHAPTER');
      expect(chapterDocs).toHaveLength(2);

      const notesDocs = chapters.filter(ch => ch.document_type === 'NOTES');
      expect(notesDocs).toHaveLength(1);

      const sheetDocs = chapters.filter(ch => ch.document_type === 'CHARACTER_SHEET');
      expect(sheetDocs).toHaveLength(1);
    });
  });
});
