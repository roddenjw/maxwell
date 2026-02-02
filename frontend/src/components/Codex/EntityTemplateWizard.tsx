/**
 * EntityTemplateWizard - Guided entity creation with templates
 * Step-by-step wizard that walks users through creating structured entities
 */

import { useState } from 'react';
import { EntityType, TemplateType } from '@/types/codex';
import { codexApi } from '@/lib/api';
import { toast } from '@/stores/toastStore';

interface EntityTemplateWizardProps {
  manuscriptId: string;  // Used for future AI features
  onComplete: (entityData: {
    name: string;
    type: EntityType;
    template_type: TemplateType;
    template_data: any;
    aliases: string[];
  }) => void;
  onCancel: () => void;
}

// Type definitions for template configuration
type FieldType = 'text' | 'textarea' | 'select' | 'tags';

interface FieldConfig {
  key: string;
  label: string;
  type: FieldType;
  placeholder?: string;
  required?: boolean;
  options?: string[];
}

interface StepConfig {
  id: string;
  title: string;
  description: string;
  fields: FieldConfig[];
}

interface TemplateConfig {
  label: string;
  icon: string;
  entityType: EntityType;
  description: string;
  steps: StepConfig[];
}

// Supported template types (excludes CUSTOM which doesn't have a config)
type SupportedTemplateType = Exclude<TemplateType, TemplateType.CUSTOM>;

// Template definitions with steps and fields
const TEMPLATE_CONFIGS: Record<SupportedTemplateType, TemplateConfig> = {
  [TemplateType.CHARACTER]: {
    label: 'Character',
    icon: '👤',
    entityType: EntityType.CHARACTER,
    description: 'Create a character with personality, backstory, and motivation',
    steps: [
      {
        id: 'basics',
        title: 'The Basics',
        description: "Let's start with who this character is",
        fields: [
          { key: 'name', label: 'Name', type: 'text', placeholder: 'Character name', required: true },
          { key: 'role', label: 'Role in Story', type: 'select', options: ['Protagonist', 'Antagonist', 'Supporting', 'Minor', 'Mentor', 'Love Interest', 'Comic Relief'] },
          { key: 'aliases', label: 'Aliases/Nicknames', type: 'text', placeholder: 'Comma-separated nicknames' },
        ],
      },
      {
        id: 'physical',
        title: 'Physical Appearance',
        description: 'How does this character look?',
        fields: [
          { key: 'physical.age', label: 'Age', type: 'text', placeholder: 'e.g., 32, early 40s, immortal' },
          { key: 'physical.appearance', label: 'General Appearance', type: 'textarea', placeholder: 'Height, build, hair, eyes, skin tone...' },
          { key: 'physical.distinguishing_features', label: 'Distinguishing Features', type: 'textarea', placeholder: 'Scars, birthmarks, unique traits...' },
        ],
      },
      {
        id: 'personality',
        title: 'Personality',
        description: "What makes this character tick?",
        fields: [
          { key: 'personality.traits', label: 'Key Traits', type: 'tags', placeholder: 'Add personality traits' },
          { key: 'personality.strengths', label: 'Strengths', type: 'textarea', placeholder: 'What are they good at?' },
          { key: 'personality.flaws', label: 'Flaws', type: 'textarea', placeholder: 'What holds them back?' },
        ],
      },
      {
        id: 'backstory',
        title: 'Backstory',
        description: 'Where do they come from?',
        fields: [
          { key: 'backstory.origin', label: 'Origin', type: 'textarea', placeholder: 'Where are they from? What was their childhood like?' },
          { key: 'backstory.key_events', label: 'Key Life Events', type: 'textarea', placeholder: 'Formative experiences that shaped them' },
          { key: 'backstory.secrets', label: 'Secrets', type: 'textarea', placeholder: 'What are they hiding?' },
        ],
      },
      {
        id: 'motivation',
        title: 'Motivation',
        description: 'What drives this character?',
        fields: [
          { key: 'motivation.want', label: 'What They Want', type: 'textarea', placeholder: 'Their conscious goal or desire' },
          { key: 'motivation.need', label: 'What They Need', type: 'textarea', placeholder: 'What they actually need (often different from want)' },
        ],
      },
    ],
  },
  [TemplateType.LOCATION]: {
    label: 'Location',
    icon: '📍',
    entityType: EntityType.LOCATION,
    description: 'Create a place with atmosphere, history, and secrets',
    steps: [
      {
        id: 'basics',
        title: 'The Basics',
        description: "What is this place?",
        fields: [
          { key: 'name', label: 'Name', type: 'text', placeholder: 'Location name', required: true },
          { key: 'type', label: 'Type', type: 'select', options: ['City', 'Town', 'Village', 'Castle', 'Fortress', 'Forest', 'Mountain', 'Desert', 'Ocean', 'Island', 'Building', 'Room', 'Other'] },
          { key: 'aliases', label: 'Other Names', type: 'text', placeholder: 'Historical names, nicknames' },
        ],
      },
      {
        id: 'geography',
        title: 'Geography',
        description: 'The physical aspects of this place',
        fields: [
          { key: 'geography.terrain', label: 'Terrain', type: 'textarea', placeholder: 'Mountains, rivers, forests...' },
          { key: 'geography.climate', label: 'Climate', type: 'text', placeholder: 'Weather patterns, seasons' },
          { key: 'geography.size', label: 'Size/Scale', type: 'text', placeholder: 'How big is it?' },
        ],
      },
      {
        id: 'atmosphere',
        title: 'Atmosphere',
        description: 'What does it feel like to be here?',
        fields: [
          { key: 'atmosphere.mood', label: 'Mood/Feeling', type: 'textarea', placeholder: 'The emotional quality of the place' },
          { key: 'atmosphere.sounds', label: 'Sounds', type: 'textarea', placeholder: 'What do you hear?' },
          { key: 'atmosphere.smells', label: 'Smells', type: 'textarea', placeholder: 'What scents fill the air?' },
        ],
      },
      {
        id: 'history',
        title: 'History',
        description: "This place's past",
        fields: [
          { key: 'history.founded', label: 'Founded/Created', type: 'text', placeholder: 'When and how did it come to be?' },
          { key: 'history.key_events', label: 'Key Events', type: 'textarea', placeholder: 'Important things that happened here' },
          { key: 'history.current_state', label: 'Current State', type: 'textarea', placeholder: 'What is it like now?' },
        ],
      },
      {
        id: 'details',
        title: 'Details',
        description: 'Notable aspects',
        fields: [
          { key: 'notable_features', label: 'Notable Features', type: 'tags', placeholder: 'Add notable features' },
          { key: 'inhabitants', label: 'Inhabitants', type: 'textarea', placeholder: 'Who lives or works here?' },
          { key: 'secrets', label: 'Secrets', type: 'textarea', placeholder: 'Hidden aspects of this place' },
        ],
      },
    ],
  },
  [TemplateType.ITEM]: {
    label: 'Item',
    icon: '⚔️',
    entityType: EntityType.ITEM,
    description: 'Create an object with history, powers, and significance',
    steps: [
      {
        id: 'basics',
        title: 'The Basics',
        description: 'What is this item?',
        fields: [
          { key: 'name', label: 'Name', type: 'text', placeholder: 'Item name', required: true },
          { key: 'type', label: 'Type', type: 'select', options: ['Weapon', 'Armor', 'Artifact', 'Tool', 'Jewelry', 'Clothing', 'Vehicle', 'Document', 'Other'] },
          { key: 'aliases', label: 'Other Names', type: 'text', placeholder: 'Nicknames, titles' },
        ],
      },
      {
        id: 'origin',
        title: 'Origin',
        description: 'Where did this item come from?',
        fields: [
          { key: 'origin.creator', label: 'Creator', type: 'text', placeholder: 'Who made it?' },
          { key: 'origin.creation_date', label: 'When Created', type: 'text', placeholder: 'Date or era' },
          { key: 'origin.creation_story', label: 'Creation Story', type: 'textarea', placeholder: 'How and why was it made?' },
        ],
      },
      {
        id: 'properties',
        title: 'Properties',
        description: 'What can this item do?',
        fields: [
          { key: 'properties.physical_description', label: 'Physical Description', type: 'textarea', placeholder: 'What does it look like?' },
          { key: 'properties.powers', label: 'Powers/Abilities', type: 'textarea', placeholder: 'What can it do?' },
          { key: 'properties.limitations', label: 'Limitations', type: 'textarea', placeholder: 'What are its weaknesses or restrictions?' },
        ],
      },
      {
        id: 'history',
        title: 'History',
        description: "The item's journey through time",
        fields: [
          { key: 'history.previous_owners', label: 'Previous Owners', type: 'textarea', placeholder: 'Who has possessed it?' },
          { key: 'history.notable_events', label: 'Notable Events', type: 'textarea', placeholder: 'Important moments in its history' },
        ],
      },
      {
        id: 'current',
        title: 'Current State',
        description: 'Where is it now?',
        fields: [
          { key: 'current_owner', label: 'Current Owner', type: 'text', placeholder: 'Who has it now?' },
          { key: 'significance', label: 'Story Significance', type: 'textarea', placeholder: 'Why does this item matter to your story?' },
        ],
      },
    ],
  },
  [TemplateType.MAGIC_SYSTEM]: {
    label: 'Magic System',
    icon: '✨',
    entityType: EntityType.LORE,
    description: 'Design a magic system with rules, costs, and limitations',
    steps: [
      {
        id: 'basics',
        title: 'The Basics',
        description: 'What is this magic system?',
        fields: [
          { key: 'name', label: 'Name', type: 'text', placeholder: 'Magic system name', required: true },
          { key: 'source', label: 'Source of Magic', type: 'textarea', placeholder: 'Where does the magic come from?' },
          { key: 'aliases', label: 'Other Names', type: 'text', placeholder: 'Alternative names for this magic' },
        ],
      },
      {
        id: 'rules',
        title: 'Rules',
        description: 'How does this magic work?',
        fields: [
          { key: 'rules.how_it_works', label: 'How It Works', type: 'textarea', placeholder: 'The fundamental mechanics' },
          { key: 'rules.limitations', label: 'Limitations', type: 'textarea', placeholder: 'What can it NOT do?' },
          { key: 'rules.costs', label: 'Costs', type: 'textarea', placeholder: 'What does using magic cost the user?' },
        ],
      },
      {
        id: 'users',
        title: 'Users',
        description: 'Who can use this magic?',
        fields: [
          { key: 'users.who_can_use', label: 'Who Can Use It', type: 'textarea', placeholder: 'Is it inherited? Learned? Random?' },
          { key: 'users.how_learned', label: 'How Learned', type: 'textarea', placeholder: 'Training, rituals, innate ability?' },
          { key: 'users.organizations', label: 'Organizations', type: 'textarea', placeholder: 'Groups that practice this magic' },
        ],
      },
      {
        id: 'effects',
        title: 'Effects & Impact',
        description: 'What are the effects?',
        fields: [
          { key: 'effects', label: 'Possible Effects', type: 'tags', placeholder: 'Add magical effects' },
          { key: 'weaknesses', label: 'Weaknesses', type: 'textarea', placeholder: 'How can magic be countered or nullified?' },
          { key: 'cultural_impact', label: 'Cultural Impact', type: 'textarea', placeholder: 'How does this magic affect society?' },
        ],
      },
    ],
  },
  [TemplateType.CREATURE]: {
    label: 'Creature',
    icon: '🐉',
    entityType: EntityType.CREATURE,
    description: 'Create a creature with biology, behavior, and lore',
    steps: [
      {
        id: 'basics',
        title: 'The Basics',
        description: 'What is this creature?',
        fields: [
          { key: 'name', label: 'Name', type: 'text', placeholder: 'Creature/species name', required: true },
          { key: 'species', label: 'Species Classification', type: 'text', placeholder: 'What type of creature is it?' },
          { key: 'habitat', label: 'Habitat', type: 'text', placeholder: 'Where do they live?' },
        ],
      },
      {
        id: 'physical',
        title: 'Physical Traits',
        description: 'What do they look like?',
        fields: [
          { key: 'physical.appearance', label: 'Appearance', type: 'textarea', placeholder: 'General appearance' },
          { key: 'physical.size', label: 'Size', type: 'text', placeholder: 'How big are they?' },
          { key: 'physical.distinguishing_features', label: 'Distinguishing Features', type: 'textarea', placeholder: 'Unique physical traits' },
        ],
      },
      {
        id: 'behavior',
        title: 'Behavior',
        description: 'How do they act?',
        fields: [
          { key: 'behavior.temperament', label: 'Temperament', type: 'textarea', placeholder: 'Aggressive? Docile? Curious?' },
          { key: 'behavior.diet', label: 'Diet', type: 'text', placeholder: 'What do they eat?' },
          { key: 'behavior.social_structure', label: 'Social Structure', type: 'textarea', placeholder: 'Solitary? Pack? Hive?' },
        ],
      },
      {
        id: 'abilities',
        title: 'Abilities & Weaknesses',
        description: 'What can they do?',
        fields: [
          { key: 'abilities', label: 'Abilities', type: 'tags', placeholder: 'Add abilities' },
          { key: 'weaknesses', label: 'Weaknesses', type: 'textarea', placeholder: 'Vulnerabilities' },
          { key: 'cultural_significance', label: 'Cultural Significance', type: 'textarea', placeholder: 'How do people view this creature?' },
        ],
      },
    ],
  },
  [TemplateType.ORGANIZATION]: {
    label: 'Organization',
    icon: '🏛️',
    entityType: EntityType.LORE,
    description: 'Create a group with structure, goals, and secrets',
    steps: [
      {
        id: 'basics',
        title: 'The Basics',
        description: 'What is this organization?',
        fields: [
          { key: 'name', label: 'Name', type: 'text', placeholder: 'Organization name', required: true },
          { key: 'type', label: 'Type', type: 'select', options: ['Guild', 'Government', 'Military', 'Religious', 'Criminal', 'Academic', 'Secret Society', 'Corporation', 'Other'] },
          { key: 'purpose', label: 'Purpose', type: 'textarea', placeholder: 'What is their goal?' },
        ],
      },
      {
        id: 'structure',
        title: 'Structure',
        description: 'How is it organized?',
        fields: [
          { key: 'structure.leadership', label: 'Leadership', type: 'textarea', placeholder: 'Who leads? How are leaders chosen?' },
          { key: 'structure.hierarchy', label: 'Hierarchy', type: 'textarea', placeholder: 'Ranks, roles, divisions' },
          { key: 'structure.membership_requirements', label: 'Membership Requirements', type: 'textarea', placeholder: 'How do you join?' },
        ],
      },
      {
        id: 'history',
        title: 'History',
        description: 'Where did they come from?',
        fields: [
          { key: 'history.founding', label: 'Founding', type: 'textarea', placeholder: 'When and why was it founded?' },
          { key: 'history.key_events', label: 'Key Events', type: 'textarea', placeholder: 'Important moments in their history' },
          { key: 'history.current_status', label: 'Current Status', type: 'textarea', placeholder: 'Where do they stand now?' },
        ],
      },
      {
        id: 'relations',
        title: 'Relations & Secrets',
        description: 'Alliances and hidden agendas',
        fields: [
          { key: 'resources', label: 'Resources', type: 'textarea', placeholder: 'Money, influence, assets' },
          { key: 'allies', label: 'Allies', type: 'textarea', placeholder: 'Who are their friends?' },
          { key: 'enemies', label: 'Enemies', type: 'textarea', placeholder: 'Who opposes them?' },
          { key: 'secrets', label: 'Secrets', type: 'textarea', placeholder: 'Hidden agendas, secret activities' },
        ],
      },
    ],
  },
  [TemplateType.CULTURE]: {
    label: 'Culture',
    icon: '🏛️',
    entityType: EntityType.CULTURE,
    description: 'Create a culture with values, traditions, and social structure',
    steps: [
      {
        id: 'basics',
        title: 'The Basics',
        description: 'What is this culture?',
        fields: [
          { key: 'name', label: 'Name', type: 'text', placeholder: 'Culture name', required: true },
          { key: 'origin', label: 'Origin', type: 'textarea', placeholder: 'Where did this culture originate?' },
          { key: 'aliases', label: 'Other Names', type: 'text', placeholder: 'Alternative names, historical names' },
        ],
      },
      {
        id: 'values',
        title: 'Values & Beliefs',
        description: 'What does this culture believe in?',
        fields: [
          { key: 'values.core_beliefs', label: 'Core Beliefs', type: 'textarea', placeholder: 'Fundamental worldview and guiding principles' },
          { key: 'values.taboos', label: 'Taboos', type: 'textarea', placeholder: 'What is forbidden or shameful?' },
          { key: 'values.ideals', label: 'Ideals', type: 'textarea', placeholder: 'What virtues do they aspire to?' },
        ],
      },
      {
        id: 'society',
        title: 'Social Structure',
        description: 'How is society organized?',
        fields: [
          { key: 'society.structure', label: 'Structure', type: 'textarea', placeholder: 'Hierarchical, egalitarian, clan-based, etc.' },
          { key: 'society.roles', label: 'Roles', type: 'textarea', placeholder: 'How are roles assigned? Gender roles? Classes?' },
          { key: 'society.family_structure', label: 'Family Structure', type: 'textarea', placeholder: 'Nuclear, extended, communal? Marriage customs?' },
        ],
      },
      {
        id: 'traditions',
        title: 'Traditions',
        description: 'What customs define this culture?',
        fields: [
          { key: 'traditions.rituals', label: 'Rituals', type: 'textarea', placeholder: 'Daily, weekly, or seasonal rituals' },
          { key: 'traditions.celebrations', label: 'Celebrations', type: 'textarea', placeholder: 'Festivals, holidays, commemorations' },
          { key: 'traditions.rites_of_passage', label: 'Rites of Passage', type: 'textarea', placeholder: 'Coming of age, marriage, death customs' },
        ],
      },
      {
        id: 'expression',
        title: 'Arts & Expression',
        description: 'How does this culture express itself?',
        fields: [
          { key: 'arts.music', label: 'Music', type: 'textarea', placeholder: 'Musical traditions, instruments, styles' },
          { key: 'arts.visual_arts', label: 'Visual Arts', type: 'textarea', placeholder: 'Art styles, crafts, architecture' },
          { key: 'arts.storytelling', label: 'Storytelling', type: 'textarea', placeholder: 'Oral traditions, literature, myths' },
          { key: 'language', label: 'Language', type: 'textarea', placeholder: 'Language characteristics, idioms, accents' },
        ],
      },
      {
        id: 'context',
        title: 'Context & Conflicts',
        description: 'How does this culture fit in the world?',
        fields: [
          { key: 'religion', label: 'Religion', type: 'textarea', placeholder: 'Religious beliefs, practices, deities' },
          { key: 'conflicts', label: 'Conflicts', type: 'textarea', placeholder: 'Internal divisions, external tensions' },
          { key: 'notable_figures', label: 'Notable Figures', type: 'textarea', placeholder: 'Famous historical or mythical figures' },
        ],
      },
    ],
  },
  [TemplateType.RACE]: {
    label: 'Race/Species',
    icon: '👥',
    entityType: EntityType.RACE,
    description: 'Create a race or species with biology, abilities, and society',
    steps: [
      {
        id: 'basics',
        title: 'The Basics',
        description: 'What is this race or species?',
        fields: [
          { key: 'name', label: 'Name', type: 'text', placeholder: 'Race/species name', required: true },
          { key: 'origin.homeworld', label: 'Homeland', type: 'text', placeholder: 'Where do they come from?' },
          { key: 'aliases', label: 'Other Names', type: 'text', placeholder: 'Alternative names, slurs, nicknames' },
        ],
      },
      {
        id: 'origin',
        title: 'Origins',
        description: 'Where did this race come from?',
        fields: [
          { key: 'origin.creation_myth', label: 'Creation Myth', type: 'textarea', placeholder: 'How do they believe they came to be?' },
          { key: 'origin.evolution', label: 'Actual Origin', type: 'textarea', placeholder: 'The true history (if different from myth)' },
        ],
      },
      {
        id: 'physical',
        title: 'Physical Traits',
        description: 'What do they look like?',
        fields: [
          { key: 'physical.appearance', label: 'Appearance', type: 'textarea', placeholder: 'General appearance, skin, hair, eyes' },
          { key: 'physical.lifespan', label: 'Lifespan', type: 'text', placeholder: 'How long do they live?' },
          { key: 'physical.size_range', label: 'Size Range', type: 'text', placeholder: 'Height and build variations' },
          { key: 'physical.distinguishing_features', label: 'Distinguishing Features', type: 'textarea', placeholder: 'Unique physical traits (ears, tails, wings, etc.)' },
        ],
      },
      {
        id: 'abilities',
        title: 'Abilities & Weaknesses',
        description: 'What can they do?',
        fields: [
          { key: 'abilities.innate_powers', label: 'Innate Abilities', type: 'textarea', placeholder: 'Natural powers or talents' },
          { key: 'abilities.special_senses', label: 'Special Senses', type: 'textarea', placeholder: 'Enhanced senses, magical perception' },
          { key: 'abilities.weaknesses', label: 'Weaknesses', type: 'textarea', placeholder: 'Vulnerabilities, limitations' },
        ],
      },
      {
        id: 'society',
        title: 'Society',
        description: 'How do they live together?',
        fields: [
          { key: 'society.typical_culture', label: 'Typical Culture', type: 'textarea', placeholder: 'Common cultural traits across the race' },
          { key: 'society.government', label: 'Government', type: 'textarea', placeholder: 'How are they typically governed?' },
          { key: 'society.relations_with_others', label: 'Relations with Others', type: 'textarea', placeholder: 'How do they interact with other races?' },
        ],
      },
      {
        id: 'details',
        title: 'Additional Details',
        description: 'Other important information',
        fields: [
          { key: 'reproduction', label: 'Reproduction', type: 'textarea', placeholder: 'How do they reproduce? Family units?' },
          { key: 'notable_individuals', label: 'Notable Individuals', type: 'textarea', placeholder: 'Famous members of this race' },
          { key: 'stereotypes', label: 'Stereotypes', type: 'textarea', placeholder: 'Common misconceptions or generalizations' },
        ],
      },
    ],
  },
};

export default function EntityTemplateWizard({
  manuscriptId: _manuscriptId,  // Reserved for future AI features
  onComplete,
  onCancel,
}: EntityTemplateWizardProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<SupportedTemplateType | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [tagInput, setTagInput] = useState<Record<string, string>>({});
  const [aiLoadingField, setAiLoadingField] = useState<string | null>(null);

  const templateConfig = selectedTemplate ? TEMPLATE_CONFIGS[selectedTemplate] : null;

  // Get API key from localStorage
  const getApiKey = (): string | null => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('openrouter_api_key');
    }
    return null;
  };

  // Handle AI-assisted field generation
  const handleAIAssist = async (field: FieldConfig) => {
    const apiKey = getApiKey();
    if (!apiKey) {
      toast.error('Please set your OpenRouter API key in Settings');
      return;
    }

    const entityName = formData.name;
    if (!entityName) {
      toast.error('Please enter an entity name first');
      return;
    }

    if (!selectedTemplate || !templateConfig) return;

    setAiLoadingField(field.key);

    try {
      const result = await codexApi.generateFieldSuggestion({
        api_key: apiKey,
        entity_name: entityName,
        entity_type: templateConfig.entityType,
        template_type: selectedTemplate,
        field_path: field.key,
        existing_data: formData,
      });

      // Set the value
      if (field.type === 'tags' && Array.isArray(result.suggestion)) {
        setValue(field.key, result.suggestion);
      } else {
        setValue(field.key, result.suggestion);
      }

      toast.success(`Generated! Cost: ${result.cost.formatted}`);
    } catch (error: any) {
      console.error('AI generation failed:', error);
      if (error.message?.includes('invalid_api_key')) {
        toast.error('Invalid API key. Check your settings.');
      } else if (error.message?.includes('insufficient_credits')) {
        toast.error('Insufficient OpenRouter credits.');
      } else {
        toast.error(error.message || 'AI generation failed');
      }
    } finally {
      setAiLoadingField(null);
    }
  };
  const steps = templateConfig?.steps || [];
  const currentStepConfig = steps[currentStep];

  // Get nested value from formData
  const getValue = (key: string): any => {
    const parts = key.split('.');
    let value: any = formData;
    for (const part of parts) {
      value = value?.[part];
    }
    return value ?? '';
  };

  // Set nested value in formData
  const setValue = (key: string, value: any) => {
    const parts = key.split('.');
    setFormData((prev) => {
      const newData = { ...prev };
      let current: any = newData;
      for (let i = 0; i < parts.length - 1; i++) {
        if (!current[parts[i]]) {
          current[parts[i]] = {};
        }
        current = current[parts[i]];
      }
      current[parts[parts.length - 1]] = value;
      return newData;
    });
  };

  // Handle tag addition
  const addTag = (key: string) => {
    const input = tagInput[key]?.trim();
    if (!input) return;

    const currentTags = getValue(key) || [];
    if (!currentTags.includes(input)) {
      setValue(key, [...currentTags, input]);
    }
    setTagInput((prev) => ({ ...prev, [key]: '' }));
  };

  // Handle tag removal
  const removeTag = (key: string, index: number) => {
    const currentTags = getValue(key) || [];
    setValue(key, currentTags.filter((_: any, i: number) => i !== index));
  };

  // Check if current step is valid
  const isStepValid = (): boolean => {
    if (!currentStepConfig) return false;
    for (const field of currentStepConfig.fields) {
      if (field.required) {
        const value = getValue(field.key);
        if (!value || (typeof value === 'string' && !value.trim())) {
          return false;
        }
      }
    }
    return true;
  };

  // Handle next step
  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  // Handle previous step
  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // Handle completion
  const handleComplete = () => {
    if (!templateConfig) return;

    // Build template data from form data
    const templateData: Record<string, any> = {};
    for (const step of steps) {
      for (const field of step.fields) {
        if (field.key === 'name' || field.key === 'aliases') continue;
        const value = getValue(field.key);
        if (value && (typeof value !== 'string' || value.trim())) {
          const parts = field.key.split('.');
          if (parts.length === 1) {
            templateData[parts[0]] = value;
          } else {
            if (!templateData[parts[0]]) templateData[parts[0]] = {};
            templateData[parts[0]][parts[1]] = value;
          }
        }
      }
    }

    // Parse aliases
    const aliasesStr = formData.aliases || '';
    const aliases = aliasesStr
      .split(',')
      .map((a: string) => a.trim())
      .filter((a: string) => a.length > 0);

    onComplete({
      name: formData.name || '',
      type: templateConfig.entityType,
      template_type: selectedTemplate!,
      template_data: templateData,
      aliases,
    });
  };

  // Render field
  const renderField = (field: FieldConfig) => {
    const value = getValue(field.key);

    switch (field.type) {
      case 'text':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(field.key, e.target.value)}
            placeholder={field.placeholder}
            className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans text-midnight placeholder:text-faded-ink/50 focus:border-bronze focus:outline-none"
            style={{ borderRadius: '2px' }}
          />
        );

      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={(e) => setValue(field.key, e.target.value)}
            placeholder={field.placeholder}
            className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans text-midnight placeholder:text-faded-ink/50 focus:border-bronze focus:outline-none min-h-[80px] resize-y"
            style={{ borderRadius: '2px' }}
          />
        );

      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => setValue(field.key, e.target.value)}
            className="w-full bg-white border border-slate-ui px-3 py-2 text-sm font-sans text-midnight focus:border-bronze focus:outline-none"
            style={{ borderRadius: '2px' }}
          >
            <option value="">Select...</option>
            {field.options?.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );

      case 'tags':
        const tags = value || [];
        return (
          <div>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {tags.map((tag: string, index: number) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-bronze/10 text-bronze text-sm font-sans"
                  style={{ borderRadius: '2px' }}
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(field.key, index)}
                    className="text-bronze hover:text-red-600 font-bold"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={tagInput[field.key] || ''}
                onChange={(e) => setTagInput((prev) => ({ ...prev, [field.key]: e.target.value }))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    addTag(field.key);
                  }
                }}
                placeholder={field.placeholder}
                className="flex-1 bg-white border border-slate-ui px-3 py-2 text-sm font-sans text-midnight placeholder:text-faded-ink/50 focus:border-bronze focus:outline-none"
                style={{ borderRadius: '2px' }}
              />
              <button
                type="button"
                onClick={() => addTag(field.key)}
                className="px-3 py-2 bg-bronze text-white text-sm font-sans hover:bg-bronze/90"
                style={{ borderRadius: '2px' }}
              >
                Add
              </button>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  // Template selection screen
  if (!selectedTemplate) {
    return (
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-garamond font-bold text-midnight">
            Create New Entity
          </h3>
          <button
            onClick={onCancel}
            className="text-faded-ink hover:text-midnight text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <p className="text-sm text-faded-ink font-sans mb-4">
          Choose a template to get started. Each template guides you through creating a well-developed entity.
        </p>

        <div className="grid grid-cols-2 gap-3">
          {Object.entries(TEMPLATE_CONFIGS).map(([key, config]) => (
            <button
              key={key}
              onClick={() => setSelectedTemplate(key as SupportedTemplateType)}
              className="p-4 text-left bg-white border border-slate-ui hover:border-bronze hover:bg-bronze/5 transition-colors"
              style={{ borderRadius: '2px' }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">{config.icon}</span>
                <span className="font-garamond font-semibold text-midnight">{config.label}</span>
              </div>
              <p className="text-xs text-faded-ink font-sans">{config.description}</p>
            </button>
          ))}
        </div>

        <div className="pt-4 border-t border-slate-ui">
          <button
            onClick={onCancel}
            className="w-full px-4 py-2 bg-slate-ui text-midnight text-sm font-sans hover:bg-slate-ui/80"
            style={{ borderRadius: '2px' }}
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  // Wizard steps
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-ui bg-white">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{templateConfig?.icon}</span>
            <h3 className="text-lg font-garamond font-bold text-midnight">
              New {templateConfig?.label}
            </h3>
          </div>
          <button
            onClick={onCancel}
            className="text-faded-ink hover:text-midnight text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-1 mt-3">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={`flex-1 h-1.5 transition-colors ${
                index <= currentStep ? 'bg-bronze' : 'bg-slate-ui'
              }`}
              style={{ borderRadius: '2px' }}
            />
          ))}
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-between mt-2">
          <p className="text-xs text-faded-ink font-sans">
            Step {currentStep + 1} of {steps.length}
          </p>
          <button
            onClick={() => setSelectedTemplate(null)}
            className="text-xs text-bronze hover:underline font-sans"
          >
            Change template
          </button>
        </div>
      </div>

      {/* Step content */}
      <div className="flex-1 overflow-y-auto p-4">
        {currentStepConfig && (
          <div className="space-y-4">
            <div className="mb-4">
              <h4 className="text-base font-garamond font-semibold text-midnight">
                {currentStepConfig.title}
              </h4>
              <p className="text-sm text-faded-ink font-sans">
                {currentStepConfig.description}
              </p>
            </div>

            {currentStepConfig.fields.map((field) => {
              // Show AI button for fields that aren't name, aliases, or select
              const showAIButton = field.key !== 'name' && field.key !== 'aliases' && field.type !== 'select';
              const isLoadingThisField = aiLoadingField === field.key;

              return (
                <div key={field.key}>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-sans text-faded-ink uppercase">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    {showAIButton && (
                      <button
                        type="button"
                        onClick={() => handleAIAssist(field)}
                        disabled={isLoadingThisField || !formData.name}
                        className={`text-xs font-sans flex items-center gap-1 px-2 py-0.5 transition-colors ${
                          isLoadingThisField
                            ? 'text-purple-400 cursor-wait'
                            : !formData.name
                            ? 'text-gray-300 cursor-not-allowed'
                            : 'text-purple-600 hover:text-purple-800 hover:bg-purple-50'
                        }`}
                        style={{ borderRadius: '2px' }}
                        title={!formData.name ? 'Enter a name first' : 'Generate with AI'}
                      >
                        {isLoadingThisField ? (
                          <>
                            <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            <span>Generating...</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                            <span>AI</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                  {renderField(field)}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="p-4 border-t border-slate-ui bg-white flex gap-2">
        {currentStep > 0 && (
          <button
            onClick={handlePrevious}
            className="flex-1 px-4 py-2 bg-slate-ui text-midnight text-sm font-sans hover:bg-slate-ui/80"
            style={{ borderRadius: '2px' }}
          >
            Previous
          </button>
        )}

        {currentStep < steps.length - 1 ? (
          <button
            onClick={handleNext}
            disabled={!isStepValid()}
            className="flex-1 px-4 py-2 bg-bronze text-white text-sm font-sans hover:bg-bronze/90 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ borderRadius: '2px' }}
          >
            Next
          </button>
        ) : (
          <button
            onClick={handleComplete}
            disabled={!isStepValid()}
            className="flex-1 px-4 py-2 bg-bronze text-white text-sm font-sans hover:bg-bronze/90 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ borderRadius: '2px' }}
          >
            Create {templateConfig?.label}
          </button>
        )}
      </div>
    </div>
  );
}
