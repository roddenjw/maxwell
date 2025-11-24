/**
 * SceneBreakNode - Custom Lexical node for scene separators
 * Renders as *** centered divider
 */

import { DecoratorNode, type EditorConfig, type LexicalNode, type NodeKey, type SerializedLexicalNode, type Spread } from 'lexical';

export type SerializedSceneBreakNode = Spread<
  {
    type: 'scene-break';
    version: 1;
  },
  SerializedLexicalNode
>;

export class SceneBreakNode extends DecoratorNode<JSX.Element> {
  static getType(): string {
    return 'scene-break';
  }

  static clone(node: SceneBreakNode): SceneBreakNode {
    return new SceneBreakNode(node.__key);
  }

  static importJSON(_serializedNode: SerializedSceneBreakNode): SceneBreakNode {
    return $createSceneBreakNode();
  }

  exportJSON(): SerializedSceneBreakNode {
    return {
      type: 'scene-break',
      version: 1,
    };
  }

  createDOM(_config: EditorConfig): HTMLElement {
    const div = document.createElement('div');
    div.className = 'scene-break';
    return div;
  }

  updateDOM(): false {
    return false;
  }

  decorate(): JSX.Element {
    return <SceneBreakComponent nodeKey={this.getKey()} />;
  }

  isInline(): false {
    return false;
  }

  isIsolated(): true {
    return true;
  }

  isTopLevel(): true {
    return true;
  }
}

export function $createSceneBreakNode(): SceneBreakNode {
  return new SceneBreakNode();
}

export function $isSceneBreakNode(
  node: LexicalNode | null | undefined,
): node is SceneBreakNode {
  return node instanceof SceneBreakNode;
}

// React component that renders the scene break
function SceneBreakComponent({ nodeKey }: { nodeKey: NodeKey }) {
  return (
    <div
      className="scene-break my-8 flex items-center justify-center select-none"
      data-lexical-decorator="true"
      data-node-key={nodeKey}
    >
      <span className="text-2xl text-gray-400 dark:text-gray-600 font-mono">
        * * *
      </span>
    </div>
  );
}
