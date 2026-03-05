import { Component } from 'react'

/**
 * ErrorBoundary — catches React rendering errors and shows a fallback UI
 * instead of crashing the entire page.
 *
 * Usage:
 *   <ErrorBoundary fallbackMessage="Erro ao carregar seção">
 *     <SomeComponent />
 *   </ErrorBoundary>
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: 'var(--space-lg, 24px)',
          background: 'var(--color-surface, #fff)',
          borderRadius: 'var(--radius-md, 10px)',
          border: '1px solid var(--color-border, #e0d6cc)',
          textAlign: 'center',
        }}>
          <p style={{
            color: 'var(--color-red, #c0392b)',
            fontWeight: 600,
            marginBottom: 'var(--space-sm, 8px)',
          }}>
            {this.props.fallbackMessage || 'Algo deu errado nesta seção'}
          </p>
          <p style={{
            color: 'var(--color-text-secondary, #8c7e74)',
            fontSize: '13px',
            marginBottom: 'var(--space-md, 16px)',
          }}>
            {this.state.error?.message || 'Erro desconhecido'}
          </p>
          <button
            onClick={this.handleRetry}
            style={{
              padding: '6px 16px',
              borderRadius: 'var(--radius-sm, 6px)',
              border: '1px solid var(--color-border, #e0d6cc)',
              background: 'var(--color-bg, #f7f4f0)',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            Tentar novamente
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
