/**
 * FeatureErrorBoundary Component
 * A reusable error boundary for individual features with a friendly UI
 */

import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  featureName: string;
  onRetry?: () => void;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class FeatureErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(`${this.props.featureName} error:`, error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    this.props.onRetry?.();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 flex items-center justify-center bg-vellum p-8">
          <div className="text-center max-w-lg">
            <div className="text-6xl mb-6">⚠️</div>
            <h2 className="font-serif text-2xl font-bold text-midnight mb-4">
              Something went wrong with {this.props.featureName}
            </h2>
            <p className="font-sans text-faded-ink text-sm mb-6">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <div className="flex flex-col gap-3 items-center">
              <button
                onClick={this.handleRetry}
                className="px-6 py-3 bg-bronze hover:bg-bronze-dark text-white font-sans font-medium uppercase tracking-button transition-colors shadow-book"
                style={{ borderRadius: '2px' }}
              >
                Try Again
              </button>
              {this.props.onReset && (
                <button
                  onClick={this.handleReset}
                  className="px-6 py-3 border-2 border-bronze text-bronze hover:bg-bronze/10 font-sans font-medium uppercase tracking-button transition-colors"
                  style={{ borderRadius: '2px' }}
                >
                  Reset
                </button>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default FeatureErrorBoundary;
