/**
 * Chapter Recap Card Generator - Creates beautiful shareable cards for chapter recaps
 * Supports multiple genre-specific templates with canvas rendering
 */

import analytics from '@/lib/analytics';

export interface ChapterRecapData {
  chapter_title: string;
  chapter_number?: number;
  word_count: number;
  summary: string;
  key_events?: string[];
  emotional_tone?: string;
  memorable_quote?: string;
  themes?: string[];
  manuscript_title?: string;
}

export type ChapterTemplateType =
  | 'dark'
  | 'vintage'
  | 'neon'
  | 'manuscript'
  | 'typewriter'
  | 'fantasy'
  | 'scifi'
  | 'romance'
  | 'thriller'
  | 'literary';

interface TemplateConfig {
  bgGradient: string[];
  textColor: string;
  accentColor: string;
  secondaryColor: string;
  fontFamily: string;
  borderStyle?: 'ornate' | 'sharp' | 'minimal' | 'digital' | 'elegant';
}

export type CardFormat = 'story' | 'post';

export class ChapterRecapCardGenerator {
  private templates: Record<ChapterTemplateType, TemplateConfig> = {
    dark: {
      bgGradient: ['#1a1a2e', '#16213e', '#0f3460'],
      textColor: '#e94560',
      accentColor: '#eaeaea',
      secondaryColor: '#a8b2d1',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif',
      borderStyle: 'minimal'
    },
    vintage: {
      bgGradient: ['#f4e8c1', '#e8d5b5', '#dcc7a8'],
      textColor: '#5e3a24',
      accentColor: '#8b5a3c',
      secondaryColor: '#6d4c3d',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif',
      borderStyle: 'ornate'
    },
    neon: {
      bgGradient: ['#0a0e27', '#1e2761', '#3d5a80'],
      textColor: '#ee6c4d',
      accentColor: '#98c1d9',
      secondaryColor: '#f4a261',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif',
      borderStyle: 'digital'
    },
    manuscript: {
      bgGradient: ['#f5f0e6', '#e8dbc5', '#d4c4a8'],
      textColor: '#3e2723',
      accentColor: '#6d4c41',
      secondaryColor: '#795548',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif',
      borderStyle: 'ornate'
    },
    typewriter: {
      bgGradient: ['#fafafa', '#f0f0f0', '#e5e5e5'],
      textColor: '#1a1a1a',
      accentColor: '#333333',
      secondaryColor: '#666666',
      fontFamily: 'Courier New, Courier, monospace',
      borderStyle: 'minimal'
    },
    fantasy: {
      bgGradient: ['#2d1b4e', '#4a1942', '#6b2d5b'],
      textColor: '#ffd700',
      accentColor: '#e6be8a',
      secondaryColor: '#c9a7eb',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif',
      borderStyle: 'ornate'
    },
    scifi: {
      bgGradient: ['#0a1628', '#0d2137', '#103045'],
      textColor: '#00d4ff',
      accentColor: '#7fdbff',
      secondaryColor: '#39cccc',
      fontFamily: 'Courier New, Courier, monospace',
      borderStyle: 'digital'
    },
    romance: {
      bgGradient: ['#fff5f5', '#ffe4e6', '#fecdd3'],
      textColor: '#be185d',
      accentColor: '#ec4899',
      secondaryColor: '#f472b6',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif',
      borderStyle: 'elegant'
    },
    thriller: {
      bgGradient: ['#0f0f0f', '#1a1a1a', '#2d2d2d'],
      textColor: '#dc2626',
      accentColor: '#fafafa',
      secondaryColor: '#a3a3a3',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif',
      borderStyle: 'sharp'
    },
    literary: {
      bgGradient: ['#fefefe', '#f8f8f8', '#f2f2f2'],
      textColor: '#1f2937',
      accentColor: '#374151',
      secondaryColor: '#6b7280',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif',
      borderStyle: 'minimal'
    }
  };

  /**
   * Generate a shareable chapter recap card
   */
  async generateCard(
    recap: ChapterRecapData,
    template: ChapterTemplateType = 'dark',
    format: CardFormat = 'story'
  ): Promise<Blob> {
    const canvas = document.createElement('canvas');

    if (format === 'story') {
      canvas.width = 1080;
      canvas.height = 1920;
    } else {
      canvas.width = 1080;
      canvas.height = 1080;
    }

    const ctx = canvas.getContext('2d')!;
    const config = this.templates[template];

    // Draw background
    this.drawGradient(ctx, canvas.width, canvas.height, config.bgGradient);

    // Add decorative elements based on template
    this.drawDecorations(ctx, canvas.width, canvas.height, config);

    // Draw content
    this.drawContent(ctx, canvas.width, canvas.height, recap, config, format);

    // Convert to blob
    return new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject(new Error('Failed to generate image'));
        }
      }, 'image/png', 0.95);
    });
  }

  private drawGradient(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    colors: string[]
  ): void {
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, colors[0]);
    gradient.addColorStop(0.5, colors[1]);
    gradient.addColorStop(1, colors[2]);

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
  }

  private drawDecorations(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    config: TemplateConfig
  ): void {
    ctx.strokeStyle = config.accentColor;
    ctx.lineWidth = 2;

    switch (config.borderStyle) {
      case 'ornate':
        this.drawOrnateBorder(ctx, width, height, config);
        break;
      case 'sharp':
        this.drawSharpBorder(ctx, width, height, config);
        break;
      case 'digital':
        this.drawDigitalBorder(ctx, width, height, config);
        break;
      case 'elegant':
        this.drawElegantBorder(ctx, width, height, config);
        break;
      default:
        this.drawMinimalBorder(ctx, width, height, config);
    }

    // Add subtle texture
    this.addNoiseTexture(ctx, width, height, config);
  }

  private drawOrnateBorder(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    config: TemplateConfig
  ): void {
    ctx.globalAlpha = 0.4;
    ctx.strokeStyle = config.accentColor;
    ctx.lineWidth = 3;

    // Double border with corners
    const margin = 50;
    ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);
    ctx.lineWidth = 1;
    ctx.strokeRect(margin + 10, margin + 10, width - margin * 2 - 20, height - margin * 2 - 20);

    // Corner flourishes
    const cornerSize = 40;
    ctx.lineWidth = 2;

    // Top left
    ctx.beginPath();
    ctx.moveTo(margin, margin + cornerSize);
    ctx.quadraticCurveTo(margin, margin, margin + cornerSize, margin);
    ctx.stroke();

    // Top right
    ctx.beginPath();
    ctx.moveTo(width - margin - cornerSize, margin);
    ctx.quadraticCurveTo(width - margin, margin, width - margin, margin + cornerSize);
    ctx.stroke();

    // Bottom left
    ctx.beginPath();
    ctx.moveTo(margin, height - margin - cornerSize);
    ctx.quadraticCurveTo(margin, height - margin, margin + cornerSize, height - margin);
    ctx.stroke();

    // Bottom right
    ctx.beginPath();
    ctx.moveTo(width - margin - cornerSize, height - margin);
    ctx.quadraticCurveTo(width - margin, height - margin, width - margin, height - margin - cornerSize);
    ctx.stroke();

    ctx.globalAlpha = 1.0;
  }

  private drawSharpBorder(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    config: TemplateConfig
  ): void {
    ctx.globalAlpha = 0.5;
    ctx.strokeStyle = config.textColor;
    ctx.lineWidth = 4;

    // Sharp diagonal corners
    const margin = 40;
    const cutSize = 30;

    ctx.beginPath();
    ctx.moveTo(margin + cutSize, margin);
    ctx.lineTo(width - margin - cutSize, margin);
    ctx.lineTo(width - margin, margin + cutSize);
    ctx.lineTo(width - margin, height - margin - cutSize);
    ctx.lineTo(width - margin - cutSize, height - margin);
    ctx.lineTo(margin + cutSize, height - margin);
    ctx.lineTo(margin, height - margin - cutSize);
    ctx.lineTo(margin, margin + cutSize);
    ctx.closePath();
    ctx.stroke();

    ctx.globalAlpha = 1.0;
  }

  private drawDigitalBorder(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    config: TemplateConfig
  ): void {
    ctx.globalAlpha = 0.3;
    ctx.strokeStyle = config.textColor;

    // Grid pattern
    const gridSize = 60;
    ctx.lineWidth = 1;

    for (let x = gridSize; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    for (let y = gridSize; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Scanline effect
    ctx.globalAlpha = 0.05;
    for (let y = 0; y < height; y += 4) {
      ctx.fillStyle = config.textColor;
      ctx.fillRect(0, y, width, 2);
    }

    ctx.globalAlpha = 1.0;
  }

  private drawElegantBorder(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    config: TemplateConfig
  ): void {
    ctx.globalAlpha = 0.3;
    ctx.strokeStyle = config.textColor;
    ctx.lineWidth = 1;

    // Elegant curves
    const margin = 60;

    ctx.beginPath();
    ctx.moveTo(margin, height / 2);
    ctx.quadraticCurveTo(margin, margin, width / 2, margin);
    ctx.quadraticCurveTo(width - margin, margin, width - margin, height / 2);
    ctx.quadraticCurveTo(width - margin, height - margin, width / 2, height - margin);
    ctx.quadraticCurveTo(margin, height - margin, margin, height / 2);
    ctx.stroke();

    // Small decorative hearts/swirls
    ctx.fillStyle = config.textColor;
    ctx.globalAlpha = 0.15;

    // Top center decoration
    ctx.font = '40px serif';
    ctx.textAlign = 'center';
    ctx.fillText('~', width / 2, margin + 30);
    ctx.fillText('~', width / 2, height - margin - 10);

    ctx.globalAlpha = 1.0;
  }

  private drawMinimalBorder(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    config: TemplateConfig
  ): void {
    ctx.globalAlpha = 0.3;
    ctx.strokeStyle = config.accentColor;
    ctx.lineWidth = 2;

    // Simple corner marks
    const margin = 40;
    const markLength = 60;

    // Top left
    ctx.beginPath();
    ctx.moveTo(margin, margin + markLength);
    ctx.lineTo(margin, margin);
    ctx.lineTo(margin + markLength, margin);
    ctx.stroke();

    // Top right
    ctx.beginPath();
    ctx.moveTo(width - margin - markLength, margin);
    ctx.lineTo(width - margin, margin);
    ctx.lineTo(width - margin, margin + markLength);
    ctx.stroke();

    // Bottom left
    ctx.beginPath();
    ctx.moveTo(margin, height - margin - markLength);
    ctx.lineTo(margin, height - margin);
    ctx.lineTo(margin + markLength, height - margin);
    ctx.stroke();

    // Bottom right
    ctx.beginPath();
    ctx.moveTo(width - margin - markLength, height - margin);
    ctx.lineTo(width - margin, height - margin);
    ctx.lineTo(width - margin, height - margin - markLength);
    ctx.stroke();

    ctx.globalAlpha = 1.0;
  }

  private addNoiseTexture(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    config: TemplateConfig
  ): void {
    ctx.globalAlpha = 0.02;
    for (let i = 0; i < 800; i++) {
      const x = Math.random() * width;
      const y = Math.random() * height;
      const size = Math.random() * 2;
      ctx.fillStyle = config.accentColor;
      ctx.fillRect(x, y, size, size);
    }
    ctx.globalAlpha = 1.0;
  }

  private drawContent(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    recap: ChapterRecapData,
    config: TemplateConfig,
    format: CardFormat
  ): void {
    const isStory = format === 'story';
    let yOffset = isStory ? 150 : 100;
    const lineHeight = isStory ? 1.4 : 1.3;
    const margin = 80;
    const contentWidth = width - margin * 2;

    ctx.textAlign = 'center';

    // Chapter title
    ctx.font = `bold ${isStory ? 72 : 56}px ${config.fontFamily}`;
    ctx.fillStyle = config.textColor;
    const wrappedTitle = this.wrapText(ctx, recap.chapter_title, contentWidth);
    for (const line of wrappedTitle) {
      ctx.fillText(line, width / 2, yOffset);
      yOffset += (isStory ? 72 : 56) * lineHeight;
    }

    yOffset += 20;

    // Chapter number and word count
    ctx.font = `${isStory ? 36 : 28}px ${config.fontFamily}`;
    ctx.fillStyle = config.secondaryColor;
    const metaText = [
      recap.chapter_number ? `Chapter ${recap.chapter_number}` : null,
      `${recap.word_count.toLocaleString()} words`
    ].filter(Boolean).join(' | ');
    ctx.fillText(metaText, width / 2, yOffset);

    yOffset += isStory ? 100 : 60;

    // Summary (main content)
    ctx.font = `${isStory ? 38 : 30}px ${config.fontFamily}`;
    ctx.fillStyle = config.accentColor;

    const summaryLines = this.wrapText(ctx, recap.summary, contentWidth - 40);
    const maxSummaryLines = isStory ? 8 : 4;
    const displayLines = summaryLines.slice(0, maxSummaryLines);

    if (summaryLines.length > maxSummaryLines) {
      displayLines[displayLines.length - 1] = displayLines[displayLines.length - 1].slice(0, -3) + '...';
    }

    for (const line of displayLines) {
      ctx.fillText(line, width / 2, yOffset);
      yOffset += (isStory ? 38 : 30) * lineHeight;
    }

    yOffset += isStory ? 60 : 30;

    // Emotional tone (if available)
    if (recap.emotional_tone && isStory) {
      ctx.font = `italic ${isStory ? 32 : 26}px ${config.fontFamily}`;
      ctx.fillStyle = config.textColor;
      ctx.fillText(`Mood: ${recap.emotional_tone}`, width / 2, yOffset);
      yOffset += 80;
    }

    // Key events (if available and story format)
    if (recap.key_events && recap.key_events.length > 0 && isStory) {
      yOffset += 20;

      ctx.font = `bold 32px ${config.fontFamily}`;
      ctx.fillStyle = config.textColor;
      ctx.fillText('Key Moments', width / 2, yOffset);
      yOffset += 60;

      ctx.font = `28px ${config.fontFamily}`;
      ctx.fillStyle = config.secondaryColor;

      const maxEvents = 3;
      for (let i = 0; i < Math.min(recap.key_events.length, maxEvents); i++) {
        const eventLines = this.wrapText(ctx, `${i + 1}. ${recap.key_events[i]}`, contentWidth - 60);
        for (const line of eventLines.slice(0, 2)) {
          ctx.fillText(line, width / 2, yOffset);
          yOffset += 36;
        }
        yOffset += 10;
      }
    }

    // Memorable quote (if available)
    if (recap.memorable_quote && isStory) {
      yOffset = height - 350;

      ctx.font = `italic 36px ${config.fontFamily}`;
      ctx.fillStyle = config.accentColor;
      const quoteLines = this.wrapText(ctx, `"${recap.memorable_quote}"`, contentWidth - 60);
      for (const line of quoteLines.slice(0, 3)) {
        ctx.fillText(line, width / 2, yOffset);
        yOffset += 48;
      }
    }

    // Themes (if available)
    if (recap.themes && recap.themes.length > 0) {
      const themesY = isStory ? height - 180 : height - 120;
      ctx.font = `24px ${config.fontFamily}`;
      ctx.fillStyle = config.secondaryColor;
      const themesText = recap.themes.slice(0, 4).join(' | ');
      ctx.fillText(themesText, width / 2, themesY);
    }

    // Watermark
    ctx.font = `italic 28px ${config.fontFamily}`;
    ctx.fillStyle = config.textColor;
    ctx.globalAlpha = 0.5;
    ctx.fillText('Written in Maxwell', width / 2, height - 60);
    ctx.globalAlpha = 1.0;
  }

  private wrapText(
    ctx: CanvasRenderingContext2D,
    text: string,
    maxWidth: number
  ): string[] {
    const words = text.split(' ');
    const lines: string[] = [];
    let currentLine = '';

    for (const word of words) {
      const testLine = currentLine ? `${currentLine} ${word}` : word;
      const metrics = ctx.measureText(testLine);

      if (metrics.width > maxWidth && currentLine) {
        lines.push(currentLine);
        currentLine = word;
      } else {
        currentLine = testLine;
      }
    }

    if (currentLine) {
      lines.push(currentLine);
    }

    return lines;
  }

  /**
   * Share to social media with tracking
   */
  async shareToSocial(
    blob: Blob,
    recap: ChapterRecapData,
    platform: 'twitter' | 'facebook' | 'instagram' | 'download' | 'copy'
  ): Promise<void> {
    // Track share
    analytics.recapShared('chapter', platform);

    const file = new File([blob], `maxwell-chapter-recap.png`, { type: 'image/png' });

    // Generate share text
    const shareText = [
      `Just finished ${recap.chapter_title}!`,
      recap.word_count ? `${recap.word_count.toLocaleString()} words` : null,
      '#WritingCommunity #Maxwell',
    ].filter(Boolean).join(' ');

    switch (platform) {
      case 'twitter':
        // Open Twitter with pre-filled text
        const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}`;
        window.open(twitterUrl, '_blank');
        // Also download for manual attachment
        this.downloadFile(blob, `maxwell-chapter-recap-${Date.now()}.png`);
        break;

      case 'facebook':
        // Facebook sharing (requires downloading first for image)
        const fbUrl = `https://www.facebook.com/sharer/sharer.php?quote=${encodeURIComponent(shareText)}`;
        window.open(fbUrl, '_blank');
        this.downloadFile(blob, `maxwell-chapter-recap-${Date.now()}.png`);
        break;

      case 'instagram':
        // Instagram requires native share or download
        if (navigator.share && navigator.canShare?.({ files: [file] })) {
          await navigator.share({
            files: [file],
            title: 'My Chapter Recap',
            text: shareText
          });
        } else {
          this.downloadFile(blob, `maxwell-chapter-recap-${Date.now()}.png`);
        }
        break;

      case 'copy':
        await this.copyToClipboard(blob);
        break;

      case 'download':
      default:
        this.downloadFile(blob, `maxwell-chapter-recap-${Date.now()}.png`);
        break;
    }
  }

  private downloadFile(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async copyToClipboard(blob: Blob): Promise<void> {
    try {
      await navigator.clipboard.write([
        new ClipboardItem({
          'image/png': blob
        })
      ]);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      throw new Error('Failed to copy to clipboard. Try downloading instead.');
    }
  }

  /**
   * Get all available templates with metadata
   */
  getTemplates(): Array<{ id: ChapterTemplateType; name: string; description: string }> {
    return [
      { id: 'dark', name: 'Dark', description: 'Elegant dark mode with accent colors' },
      { id: 'vintage', name: 'Vintage', description: 'Sepia tones with classic feel' },
      { id: 'neon', name: 'Neon', description: 'Cyberpunk-inspired bright accents' },
      { id: 'manuscript', name: 'Manuscript', description: 'Handwritten parchment style' },
      { id: 'typewriter', name: 'Typewriter', description: 'B&W monospace classic' },
      { id: 'fantasy', name: 'Fantasy', description: 'Purple & gold mystical theme' },
      { id: 'scifi', name: 'Sci-Fi', description: 'Blue & cyan digital grid' },
      { id: 'romance', name: 'Romance', description: 'Soft pink elegant cursive' },
      { id: 'thriller', name: 'Thriller', description: 'Red & black sharp angles' },
      { id: 'literary', name: 'Literary', description: 'Minimalist refined design' },
    ];
  }
}

// Export singleton
export const chapterRecapCardGenerator = new ChapterRecapCardGenerator();
