/**
 * Character Archetypes and Tropes
 * Common character roles and genre-specific tropes for tagging characters
 * Inspired by storytelling conventions and TV Tropes patterns
 */

// Character story roles
export interface CharacterRole {
  id: string;
  label: string;
  description: string;
  icon: string;
}

export const CHARACTER_ROLES: CharacterRole[] = [
  {
    id: 'PROTAGONIST',
    label: 'Protagonist',
    description: 'The main character whose journey drives the story. The audience follows their perspective and growth.',
    icon: '⭐',
  },
  {
    id: 'ANTAGONIST',
    label: 'Antagonist',
    description: 'The primary opposition to the protagonist. Creates conflict and obstacles that drive the plot.',
    icon: '👿',
  },
  {
    id: 'DEUTERAGONIST',
    label: 'Deuteragonist',
    description: 'The secondary main character, often the protagonist\'s closest ally or partner.',
    icon: '🤝',
  },
  {
    id: 'MENTOR',
    label: 'Mentor',
    description: 'A wise guide who helps the protagonist learn and grow. Often provides crucial knowledge or training.',
    icon: '🧙',
  },
  {
    id: 'LOVE_INTEREST',
    label: 'Love Interest',
    description: 'A character who serves as the romantic focus for the protagonist or another major character.',
    icon: '💕',
  },
  {
    id: 'SIDEKICK',
    label: 'Sidekick',
    description: 'A loyal companion who supports the protagonist, often providing comic relief or practical help.',
    icon: '🐕',
  },
  {
    id: 'FOIL',
    label: 'Foil',
    description: 'A character who contrasts with the protagonist, highlighting their qualities through opposition.',
    icon: '🪞',
  },
  {
    id: 'CATALYST',
    label: 'Catalyst',
    description: 'A character whose arrival or actions set the plot in motion, often without being central to it.',
    icon: '⚡',
  },
  {
    id: 'TRICKSTER',
    label: 'Trickster',
    description: 'A clever, mischievous character who uses wit and deception to achieve their goals.',
    icon: '🃏',
  },
  {
    id: 'HERALD',
    label: 'Herald',
    description: 'A character who announces change or calls the protagonist to adventure.',
    icon: '📯',
  },
  {
    id: 'GUARDIAN',
    label: 'Guardian/Threshold',
    description: 'A character who tests the protagonist before allowing them to proceed on their journey.',
    icon: '🛡️',
  },
  {
    id: 'SHAPESHIFTER',
    label: 'Shapeshifter',
    description: 'A character whose loyalty or nature is uncertain, keeping the audience guessing.',
    icon: '🎭',
  },
];

// Character tropes by genre
export interface CharacterTrope {
  id: string;
  label: string;
  description: string;
  genres: string[]; // Which genres this trope is common in
}

export const CHARACTER_TROPES: CharacterTrope[] = [
  // Universal Tropes
  {
    id: 'CHOSEN_ONE',
    label: 'The Chosen One',
    description: 'A character destined by prophecy or fate to fulfill a special role.',
    genres: ['Fantasy', 'Sci-Fi', 'Adventure'],
  },
  {
    id: 'RELUCTANT_HERO',
    label: 'Reluctant Hero',
    description: 'A character who initially refuses the call to adventure but eventually accepts.',
    genres: ['Fantasy', 'Adventure', 'Thriller'],
  },
  {
    id: 'ANTI_HERO',
    label: 'Anti-Hero',
    description: 'A protagonist who lacks conventional heroic qualities like morality or idealism.',
    genres: ['Noir', 'Thriller', 'Drama', 'Fantasy'],
  },
  {
    id: 'TRAGIC_HERO',
    label: 'Tragic Hero',
    description: 'A noble character whose fatal flaw leads to their downfall.',
    genres: ['Drama', 'Tragedy', 'Literary Fiction'],
  },
  {
    id: 'BYRONIC_HERO',
    label: 'Byronic Hero',
    description: 'A charismatic but flawed character - brooding, cynical, with a dark past.',
    genres: ['Romance', 'Gothic', 'Drama'],
  },
  {
    id: 'EVERYMAN',
    label: 'Everyman',
    description: 'An ordinary person thrust into extraordinary circumstances.',
    genres: ['Thriller', 'Horror', 'Adventure'],
  },

  // Fantasy Tropes
  {
    id: 'DARK_LORD',
    label: 'Dark Lord',
    description: 'A powerful evil entity seeking domination or destruction.',
    genres: ['Fantasy', 'Epic Fantasy'],
  },
  {
    id: 'WISE_OLD_WIZARD',
    label: 'Wise Old Wizard',
    description: 'An elderly magic user who provides guidance and crucial knowledge.',
    genres: ['Fantasy'],
  },
  {
    id: 'NOBLE_SAVAGE',
    label: 'Noble Savage',
    description: 'A character from a "primitive" culture who possesses innate wisdom and virtue.',
    genres: ['Fantasy', 'Adventure'],
  },
  {
    id: 'FALLEN_NOBLE',
    label: 'Fallen Noble',
    description: 'A character of high birth who has lost their status and must rebuild.',
    genres: ['Fantasy', 'Historical', 'Drama'],
  },

  // Romance Tropes
  {
    id: 'ENEMIES_TO_LOVERS',
    label: 'Enemies to Lovers',
    description: 'Characters who start as adversaries but develop romantic feelings.',
    genres: ['Romance', 'Drama'],
  },
  {
    id: 'FRIENDS_TO_LOVERS',
    label: 'Friends to Lovers',
    description: 'Long-time friends who realize they have deeper feelings.',
    genres: ['Romance', 'Contemporary'],
  },
  {
    id: 'GRUMPY_SUNSHINE',
    label: 'Grumpy/Sunshine',
    description: 'A pessimistic character paired with an optimistic one.',
    genres: ['Romance', 'Contemporary'],
  },
  {
    id: 'FORBIDDEN_LOVE',
    label: 'Forbidden Love',
    description: 'A romance that faces external opposition due to social, cultural, or supernatural barriers.',
    genres: ['Romance', 'Drama', 'Fantasy'],
  },

  // Mystery/Thriller Tropes
  {
    id: 'HARDBOILED_DETECTIVE',
    label: 'Hardboiled Detective',
    description: 'A cynical, tough investigator who operates in morally gray territory.',
    genres: ['Mystery', 'Noir', 'Thriller'],
  },
  {
    id: 'FEMME_FATALE',
    label: 'Femme Fatale',
    description: 'A seductive, dangerous woman who uses her allure to manipulate.',
    genres: ['Noir', 'Mystery', 'Thriller'],
  },
  {
    id: 'GENTLEMAN_THIEF',
    label: 'Gentleman Thief',
    description: 'A charming criminal who steals with style and often has a code of honor.',
    genres: ['Mystery', 'Adventure', 'Heist'],
  },
  {
    id: 'FINAL_GIRL',
    label: 'Final Girl',
    description: 'The last survivor who confronts and often defeats the antagonist.',
    genres: ['Horror', 'Thriller'],
  },

  // Sci-Fi Tropes
  {
    id: 'MAD_SCIENTIST',
    label: 'Mad Scientist',
    description: 'A brilliant but unethical researcher whose experiments cause problems.',
    genres: ['Sci-Fi', 'Horror'],
  },
  {
    id: 'AI_REBELLION',
    label: 'Rebellious AI',
    description: 'An artificial intelligence that develops independence and challenges humanity.',
    genres: ['Sci-Fi'],
  },
  {
    id: 'SPACE_COWBOY',
    label: 'Space Cowboy',
    description: 'A roguish spacefarer who operates on the fringes of society.',
    genres: ['Sci-Fi', 'Space Opera'],
  },

  // Character Flaw Tropes
  {
    id: 'HAUNTED_PAST',
    label: 'Haunted by the Past',
    description: 'A character burdened by traumatic events that affect their present behavior.',
    genres: ['Drama', 'Thriller', 'Mystery'],
  },
  {
    id: 'HIDDEN_DEPTHS',
    label: 'Hidden Depths',
    description: 'A character who appears simple but reveals unexpected complexity.',
    genres: ['Drama', 'Literary Fiction'],
  },
  {
    id: 'MAGNIFICENT_BASTARD',
    label: 'Magnificent Bastard',
    description: 'A villain so clever and charismatic that audiences can\'t help but admire them.',
    genres: ['Thriller', 'Drama', 'Fantasy'],
  },
  {
    id: 'HEART_OF_GOLD',
    label: 'Heart of Gold',
    description: 'A character with a rough exterior who proves to be kind and caring underneath.',
    genres: ['Drama', 'Romance', 'Adventure'],
  },
];

// Get roles as options for select
export function getRoleOptions() {
  return CHARACTER_ROLES.map(role => ({
    value: role.id,
    label: `${role.icon} ${role.label}`,
    description: role.description,
  }));
}

// Get tropes filtered by genre
export function getTropesByGenre(genre: string): CharacterTrope[] {
  if (!genre) return CHARACTER_TROPES;
  return CHARACTER_TROPES.filter(trope =>
    trope.genres.some(g => g.toLowerCase() === genre.toLowerCase())
  );
}

// Get tropes as options for select
export function getTropeOptions(genre?: string) {
  const tropes = genre ? getTropesByGenre(genre) : CHARACTER_TROPES;
  return tropes.map(trope => ({
    value: trope.id,
    label: trope.label,
    description: trope.description,
    genres: trope.genres,
  }));
}

// Get role by ID
export function getRoleById(id: string): CharacterRole | undefined {
  return CHARACTER_ROLES.find(role => role.id === id);
}

// Get trope by ID
export function getTropeById(id: string): CharacterTrope | undefined {
  return CHARACTER_TROPES.find(trope => trope.id === id);
}

// Format roles/tropes for AI context
export function formatArchetypesForAI(
  role?: string,
  tropes?: string[]
): string {
  const parts: string[] = [];

  if (role) {
    const roleData = getRoleById(role);
    if (roleData) {
      parts.push(`Story Role: ${roleData.label} - ${roleData.description}`);
    }
  }

  if (tropes && tropes.length > 0) {
    const tropeDescriptions = tropes
      .map(id => getTropeById(id))
      .filter(Boolean)
      .map(t => `${t!.label}: ${t!.description}`);

    if (tropeDescriptions.length > 0) {
      parts.push(`Character Tropes:\n${tropeDescriptions.join('\n')}`);
    }
  }

  return parts.join('\n\n');
}
