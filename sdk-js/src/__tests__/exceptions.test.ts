/**
 * Test exception classes
 */

import {
  UniversalAgentConnectorError,
  APIError,
  AuthenticationError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ConnectionError
} from '../exceptions';

describe('Exception Classes', () => {
  describe('UniversalAgentConnectorError', () => {
    it('should create base exception', () => {
      const error = new UniversalAgentConnectorError('Base error');
      expect(error).toBeInstanceOf(Error);
      expect(error).toBeInstanceOf(UniversalAgentConnectorError);
      expect(error.message).toBe('Base error');
      expect(error.name).toBe('UniversalAgentConnectorError');
    });
  });

  describe('APIError', () => {
    it('should create API error with status code', () => {
      const error = new APIError('API error', 500, { message: 'Error' });
      expect(error).toBeInstanceOf(UniversalAgentConnectorError);
      expect(error).toBeInstanceOf(APIError);
      expect(error.message).toBe('API error');
      expect(error.statusCode).toBe(500);
      expect(error.response).toEqual({ message: 'Error' });
    });

    it('should create API error without status code', () => {
      const error = new APIError('API error');
      expect(error.statusCode).toBeUndefined();
      expect(error.response).toBeUndefined();
    });
  });

  describe('AuthenticationError', () => {
    it('should create authentication error', () => {
      const error = new AuthenticationError('Auth failed', 401);
      expect(error).toBeInstanceOf(APIError);
      expect(error).toBeInstanceOf(UniversalAgentConnectorError);
      expect(error.message).toBe('Auth failed');
      expect(error.statusCode).toBe(401);
      expect(error.name).toBe('AuthenticationError');
    });

    it('should use default message', () => {
      const error = new AuthenticationError();
      expect(error.message).toBe('Authentication failed. Check your API key.');
      expect(error.statusCode).toBe(401);
    });
  });

  describe('NotFoundError', () => {
    it('should create not found error', () => {
      const error = new NotFoundError('Not found', 404);
      expect(error).toBeInstanceOf(APIError);
      expect(error).toBeInstanceOf(UniversalAgentConnectorError);
      expect(error.message).toBe('Not found');
      expect(error.statusCode).toBe(404);
      expect(error.name).toBe('NotFoundError');
    });

    it('should use default message', () => {
      const error = new NotFoundError();
      expect(error.message).toBe('Resource not found');
      expect(error.statusCode).toBe(404);
    });
  });

  describe('ValidationError', () => {
    it('should create validation error', () => {
      const error = new ValidationError('Invalid input', 400);
      expect(error).toBeInstanceOf(APIError);
      expect(error).toBeInstanceOf(UniversalAgentConnectorError);
      expect(error.message).toBe('Invalid input');
      expect(error.statusCode).toBe(400);
      expect(error.name).toBe('ValidationError');
    });

    it('should use default message', () => {
      const error = new ValidationError();
      expect(error.message).toBe('Validation error');
      expect(error.statusCode).toBe(400);
    });
  });

  describe('RateLimitError', () => {
    it('should create rate limit error', () => {
      const error = new RateLimitError('Rate limit exceeded', 429);
      expect(error).toBeInstanceOf(APIError);
      expect(error).toBeInstanceOf(UniversalAgentConnectorError);
      expect(error.message).toBe('Rate limit exceeded');
      expect(error.statusCode).toBe(429);
      expect(error.name).toBe('RateLimitError');
    });

    it('should use default message', () => {
      const error = new RateLimitError();
      expect(error.message).toBe('Rate limit exceeded');
      expect(error.statusCode).toBe(429);
    });
  });

  describe('ConnectionError', () => {
    it('should create connection error', () => {
      const error = new ConnectionError('Connection failed');
      expect(error).toBeInstanceOf(UniversalAgentConnectorError);
      expect(error).not.toBeInstanceOf(APIError);
      expect(error.message).toBe('Connection failed');
      expect(error.name).toBe('ConnectionError');
    });
  });

  describe('Exception Inheritance', () => {
    it('should verify inheritance chain', () => {
      const authError = new AuthenticationError('Test');
      expect(authError).toBeInstanceOf(APIError);
      expect(authError).toBeInstanceOf(UniversalAgentConnectorError);
      expect(authError).toBeInstanceOf(Error);

      const notFound = new NotFoundError('Test');
      expect(notFound).toBeInstanceOf(APIError);
      expect(notFound).toBeInstanceOf(UniversalAgentConnectorError);

      const connError = new ConnectionError('Test');
      expect(connError).toBeInstanceOf(UniversalAgentConnectorError);
      expect(connError).not.toBeInstanceOf(APIError);
    });
  });

  describe('Exception Usage', () => {
    it('should catch base exception', () => {
      try {
        throw new UniversalAgentConnectorError('Base error');
      } catch (error) {
        expect(error).toBeInstanceOf(UniversalAgentConnectorError);
        expect((error as Error).message).toBe('Base error');
      }
    });

    it('should catch specific exception', () => {
      try {
        throw new NotFoundError('Not found', 404);
      } catch (error) {
        expect(error).toBeInstanceOf(NotFoundError);
        expect((error as NotFoundError).statusCode).toBe(404);
      }
    });

    it('should catch parent exception', () => {
      try {
        throw new AuthenticationError('Auth failed', 401);
      } catch (error) {
        expect(error).toBeInstanceOf(APIError);
        expect(error).toBeInstanceOf(AuthenticationError);
        expect((error as APIError).statusCode).toBe(401);
      }
    });

    it('should handle exception with response data', () => {
      const responseData = {
        error: 'Invalid request',
        details: { field: 'email', issue: 'invalid format' }
      };
      const error = new ValidationError('Validation failed', 400, responseData);

      expect(error.response).toEqual(responseData);
      expect(error.response?.error).toBe('Invalid request');
      expect(error.response?.details).toBeDefined();
    });
  });
});

