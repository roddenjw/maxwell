/**
 * EntityMentionNode - Custom Lexical node for entity mentions
 * Makes character/location names clickable with hover preview
 */

import {
  DecoratorNode,
  type EditorConfig,
  type LexicalNode,
  type NodeKey,
  type SerializedLexicalNode,
  type Spread,
} from 'lexical';

export type EntityType = 'CHARACTER' | 'LOCATION' | 'ITEM' | 'LORE';

export type SerializedEntityMentionNode = Spread<
  {
    entityId: string;
    entityName: string;
    entityType: EntityType;
    type: 'entity-mention';
    version: 1;
  },
  SerializedLexicalNode
>;

export class EntityMentionNode extends DecoratorNode<JSX.Element> {
  __entityId: string;
  __entityName: string;
  __entityType: EntityType;

  static getType(): string {
    return 'entity-mention';
  }

  static clone(node: EntityMentionNode): EntityMentionNode {
    return new EntityMentionNode(
      node.__entityId,
      node.__entityName,
      node.__entityType,
      node.__key,
    );
  }

  static importJSON(serializedNode: SerializedEntityMentionNode): EntityMentionNode {
    const node = $createEntityMentionNode(
      serializedNode.entityId,
      serializedNode.entityName,
      serializedNode.entityType,
    );
    return node;
  }

  constructor(entityId: string, entityName: string, entityType: EntityType, key?: NodeKey) {
    super(key);
    this.__entityId = entityId;
    this.__entityName = entityName;
    this.__entityType = entityType;
  }

  exportJSON(): SerializedEntityMentionNode {
    return {
      entityId: this.__entityId,
      entityName: this.__entityName,
      entityType: this.__entityType,
      type: 'entity-mention',
      version: 1,
    };
  }

  createDOM(_config: EditorConfig): HTMLElement {
    const span = document.createElement('span');
    span.className = 'entity-mention';
    return span;
  }

  updateDOM(): false {
    return false;
  }

  decorate(): JSX.Element {
    return (
      <EntityMentionComponent
        nodeKey={this.getKey()}
        entityId={this.__entityId}
        entityName={this.__entityName}
        entityType={this.__entityType}
      />
    );
  }

  getEntityId(): string {
    return this.__entityId;
  }

  getEntityName(): string {
    return this.__entityName;
  }

  getEntityType(): EntityType {
    return this.__entityType;
  }
}

export function $createEntityMentionNode(
  entityId: string,
  entityName: string,
  entityType: EntityType,
): EntityMentionNode {
  return new EntityMentionNode(entityId, entityName, entityType);
}

export function $isEntityMentionNode(
  node: LexicalNode | null | undefined,
): node is EntityMentionNode {
  return node instanceof EntityMentionNode;
}

// React component that renders the entity mention
interface EntityMentionComponentProps {
  nodeKey: NodeKey;
  entityId: string;
  entityName: string;
  entityType: EntityType;
}

function EntityMentionComponent({
  nodeKey,
  entityId,
  entityName,
  entityType,
}: EntityMentionComponentProps) {
  const handleClick = () => {
    // TODO: Open entity details panel
    console.log('Entity clicked:', { entityId, entityName, entityType });
  };

  const getTypeColor = () => {
    switch (entityType) {
      case 'CHARACTER':
        return 'border-primary-500';
      case 'LOCATION':
        return 'border-green-500';
      case 'ITEM':
        return 'border-yellow-500';
      case 'LORE':
        return 'border-purple-500';
      default:
        return 'border-gray-500';
    }
  };

  return (
    <span
      className={`entity-mention cursor-pointer border-b-2 border-dotted ${getTypeColor()} hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors`}
      onClick={handleClick}
      data-lexical-decorator="true"
      data-node-key={nodeKey}
      data-entity-id={entityId}
      data-entity-type={entityType}
      title={`${entityType}: ${entityName}`}
    >
      {entityName}
    </span>
  );
}
