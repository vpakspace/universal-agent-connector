/**
 * Universal Agent Connector JavaScript/TypeScript SDK
 * 
 * Official SDK for the Universal Agent Connector API.
 * Provides easy integration with AI agent management, database connections, and query execution.
 */

export { UniversalAgentConnector } from './client';
export {
  UniversalAgentConnectorError,
  APIError,
  AuthenticationError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ConnectionError
} from './exceptions';

// Re-export types
export type * from './types';

