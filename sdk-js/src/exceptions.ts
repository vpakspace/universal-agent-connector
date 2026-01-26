/**
 * Exception classes for Universal Agent Connector SDK
 */

export class UniversalAgentConnectorError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UniversalAgentConnectorError';
    Object.setPrototypeOf(this, UniversalAgentConnectorError.prototype);
  }
}

export class APIError extends UniversalAgentConnectorError {
  public readonly statusCode?: number;
  public readonly response?: any;

  constructor(message: string, statusCode?: number, response?: any) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.response = response;
    Object.setPrototypeOf(this, APIError.prototype);
  }
}

export class AuthenticationError extends APIError {
  constructor(message: string = 'Authentication failed. Check your API key.', statusCode: number = 401, response?: any) {
    super(message, statusCode, response);
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

export class NotFoundError extends APIError {
  constructor(message: string = 'Resource not found', statusCode: number = 404, response?: any) {
    super(message, statusCode, response);
    this.name = 'NotFoundError';
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}

export class ValidationError extends APIError {
  constructor(message: string = 'Validation error', statusCode: number = 400, response?: any) {
    super(message, statusCode, response);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

export class RateLimitError extends APIError {
  constructor(message: string = 'Rate limit exceeded', statusCode: number = 429, response?: any) {
    super(message, statusCode, response);
    this.name = 'RateLimitError';
    Object.setPrototypeOf(this, RateLimitError.prototype);
  }
}

export class ConnectionError extends UniversalAgentConnectorError {
  constructor(message: string) {
    super(message);
    this.name = 'ConnectionError';
    Object.setPrototypeOf(this, ConnectionError.prototype);
  }
}

