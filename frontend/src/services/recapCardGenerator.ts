/**
 * Recap Card Generator - Creates beautiful shareable "Wrapped" style cards
 * Uses Canvas API to generate aesthetic images with writing stats
 */

export interface WritingStats {
  timeframe: string;
  timeframe_label: string;
  word_count: number;
  character_count: number;
  paragraph_count: number;
  session_count: number;
  sensory_words: Record<string, Array<[string, number]>>;
  most_used_word: string | null;
  writing_vibe: string;
  avg_words_per_session: number;
  writing_days: number;
  longest_streak: number;
  total_words: number;
  total_chapters: number;
}

export type TemplateType = 'dark' | 'vintage' | 'neon';

interface TemplateConfig {
  bgGradient: string[];
  textColor: string;
  accentColor: string;
  secondaryColor: string;
  fontFamily: string;
}

export class RecapCardGenerator {
  private templates: Record<TemplateType, TemplateConfig> = {
    dark: {
      bgGradient: ['#1a1a2e', '#16213e', '#0f3460'],
      textColor: '#e94560',
      accentColor: '#eaeaea',
      secondaryColor: '#a8b2d1',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif'
    },
    vintage: {
      bgGradient: ['#f4e8c1', '#e8d5b5', '#dcc7a8'],
      textColor: '#5e3a24',
      accentColor: '#8b5a3c',
      secondaryColor: '#6d4c3d',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif'
    },
    neon: {
      bgGradient: ['#0a0e27', '#1e2761', '#3d5a80'],
      textColor: '#ee6c4d',
      accentColor: '#98c1d9',
      secondaryColor: '#f4a261',
      fontFamily: 'EB Garamond, Garamond, Georgia, serif'
    }
  };

  /**
   * Generate a shareable recap card
   */
  async generateCard(
    stats: WritingStats,
    template: TemplateType = 'dark',
    format: 'instagram_story' | 'square' = 'instagram_story'
  ): Promise<Blob> {
    // Create canvas
    const canvas = document.createElement('canvas');

    if (format === 'instagram_story') {
      canvas.width = 1080;
      canvas.height = 1920;
    } else {
      canvas.width = 1080;
      canvas.height = 1080;
    }

    const ctx = canvas.getContext('2d')!;
    const config = this.templates[template];

    // Draw gradient background
    this.drawGradient(ctx, canvas.width, canvas.height, config.bgGradient);

    // Add decorative elements
    this.drawDecorativeElements(ctx, canvas.width, canvas.height, config);

    // Draw content
    let yOffset = 150;

    // Title
    ctx.font = `bold 80px ${config.fontFamily}`;
    ctx.fillStyle = config.textColor;
    ctx.textAlign = 'center';
    ctx.fillText('Your Writing Wrapped', canvas.width / 2, yOffset);
    yOffset += 80;

    // Timeframe subtitle
    ctx.font = `40px ${config.fontFamily}`;
    ctx.fillStyle = config.secondaryColor;
    ctx.fillText(stats.timeframe_label, canvas.width / 2, yOffset);
    yOffset += 150;

    // Main stat - Word count
    ctx.font = `bold 140px ${config.fontFamily}`;
    ctx.fillStyle = config.accentColor;
    ctx.fillText(stats.word_count.toLocaleString(), canvas.width / 2, yOffset);
    yOffset += 100;

    ctx.font = `45px ${config.fontFamily}`;
    ctx.fillStyle = config.textColor;
    ctx.fillText('words written', canvas.width / 2, yOffset);
    yOffset += 140;

    // Sensory word highlight
    if (stats.sensory_words && Object.keys(stats.sensory_words).length > 0) {
      const [sense, words] = Object.entries(stats.sensory_words)[0];
      const topWord = words[0][0];

      ctx.font = `40px ${config.fontFamily}`;
      ctx.fillStyle = config.secondaryColor;
      ctx.fillText(`Most used ${sense} word:`, canvas.width / 2, yOffset);
      yOffset += 80;

      ctx.font = `bold 65px ${config.fontFamily}`;
      ctx.fillStyle = config.accentColor;
      ctx.fillText(`"${topWord}"`, canvas.width / 2, yOffset);
      yOffset += 120;
    }

    // Writing vibe
    ctx.font = `bold 65px ${config.fontFamily}`;
    ctx.fillStyle = config.textColor;
    ctx.fillText(`Writing Vibe: ${stats.writing_vibe}`, canvas.width / 2, yOffset);
    yOffset += 140;

    // Secondary stats (in a box)
    const statsBoxY = yOffset;
    const statsBoxHeight = 280;
    const statsBoxPadding = 40;

    // Semi-transparent box
    ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
    ctx.fillRect(80, statsBoxY, canvas.width - 160, statsBoxHeight);

    // Stats in columns
    ctx.font = `35px ${config.fontFamily}`;
    ctx.textAlign = 'left';

    const leftX = 140;
    const rightX = canvas.width / 2 + 80;
    let statsY = statsBoxY + 70;

    // Left column
    ctx.fillStyle = config.secondaryColor;
    ctx.fillText('Sessions:', leftX, statsY);
    ctx.fillStyle = config.accentColor;
    ctx.fillText(stats.session_count.toString(), leftX + 200, statsY);

    statsY += 70;
    ctx.fillStyle = config.secondaryColor;
    ctx.fillText('Paragraphs:', leftX, statsY);
    ctx.fillStyle = config.accentColor;
    ctx.fillText(stats.paragraph_count.toString(), leftX + 200, statsY);

    statsY += 70;
    ctx.fillStyle = config.secondaryColor;
    ctx.fillText('Writing Days:', leftX, statsY);
    ctx.fillStyle = config.accentColor;
    ctx.fillText(stats.writing_days.toString(), leftX + 200, statsY);

    // Right column
    statsY = statsBoxY + 70;
    ctx.fillStyle = config.secondaryColor;
    ctx.fillText('Avg/Session:', rightX, statsY);
    ctx.fillStyle = config.accentColor;
    ctx.fillText(stats.avg_words_per_session.toString(), rightX + 200, statsY);

    statsY += 70;
    ctx.fillStyle = config.secondaryColor;
    ctx.fillText('Longest Streak:', rightX, statsY);
    ctx.fillStyle = config.accentColor;
    ctx.fillText(`${stats.longest_streak} days`, rightX + 200, statsY);

    statsY += 70;
    ctx.fillStyle = config.secondaryColor;
    ctx.fillText('Total Words:', rightX, statsY);
    ctx.fillStyle = config.accentColor;
    ctx.fillText(stats.total_words.toLocaleString(), rightX + 200, statsY);

    // Watermark
    ctx.textAlign = 'center';
    ctx.font = `italic 40px ${config.fontFamily}`;
    ctx.fillStyle = config.textColor;
    ctx.globalAlpha = 0.5;
    ctx.fillText('Written in Maxwell', canvas.width / 2, canvas.height - 80);
    ctx.globalAlpha = 1.0;

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

  /**
   * Draw gradient background
   */
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

  /**
   * Draw decorative elements (subtle texture)
   */
  private drawDecorativeElements(
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    config: TemplateConfig
  ): void {
    // Add subtle noise texture
    ctx.globalAlpha = 0.03;
    for (let i = 0; i < 1000; i++) {
      const x = Math.random() * width;
      const y = Math.random() * height;
      const size = Math.random() * 2;

      ctx.fillStyle = config.accentColor;
      ctx.fillRect(x, y, size, size);
    }
    ctx.globalAlpha = 1.0;

    // Add decorative corner flourishes
    ctx.strokeStyle = config.accentColor;
    ctx.lineWidth = 3;
    ctx.globalAlpha = 0.3;

    // Top left corner
    ctx.beginPath();
    ctx.moveTo(40, 80);
    ctx.lineTo(40, 40);
    ctx.lineTo(80, 40);
    ctx.stroke();

    // Top right corner
    ctx.beginPath();
    ctx.moveTo(width - 40, 80);
    ctx.lineTo(width - 40, 40);
    ctx.lineTo(width - 80, 40);
    ctx.stroke();

    // Bottom left corner
    ctx.beginPath();
    ctx.moveTo(40, height - 80);
    ctx.lineTo(40, height - 40);
    ctx.lineTo(80, height - 40);
    ctx.stroke();

    // Bottom right corner
    ctx.beginPath();
    ctx.moveTo(width - 40, height - 80);
    ctx.lineTo(width - 40, height - 40);
    ctx.lineTo(width - 80, height - 40);
    ctx.stroke();

    ctx.globalAlpha = 1.0;
  }

  /**
   * Share to social media or download
   */
  async shareToSocial(blob: Blob, stats: WritingStats): Promise<void> {
    const file = new File([blob], 'maxwell-recap.png', { type: 'image/png' });

    // Try native share API first (works on mobile and some desktop browsers)
    if (navigator.share && navigator.canShare?.({ files: [file] })) {
      try {
        await navigator.share({
          files: [file],
          title: 'My Writing Progress',
          text: `I wrote ${stats.word_count.toLocaleString()} words ${stats.timeframe_label.toLowerCase()}! #WritingCommunity #Maxwell`
        });
        return;
      } catch (err) {
        // User cancelled or share failed, fall through to download
        if ((err as Error).name === 'AbortError') {
          return;
        }
      }
    }

    // Fallback: Download file
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `maxwell-recap-${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Copy image to clipboard
   */
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
}
