/**
 * Tests for config command
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { configCommand } = require('../../lib/commands/config');

jest.mock('fs');
jest.mock('inquirer');

describe('Config Command', () => {
  let consoleLogSpy;
  let consoleErrorSpy;
  let processExitSpy;

  beforeEach(() => {
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    processExitSpy = jest.spyOn(process, 'exit').mockImplementation();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('should list configuration', async () => {
    const mockConfig = {
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent'
    };

    fs.existsSync.mockReturnValue(true);
    fs.readFileSync.mockReturnValue(JSON.stringify(mockConfig));

    await configCommand({ list: true });

    expect(consoleLogSpy).toHaveBeenCalled();
  });

  test('should get configuration value', async () => {
    const mockConfig = {
      url: 'http://localhost:5000',
      apiKey: 'test-key-12345'
    };

    fs.existsSync.mockReturnValue(true);
    fs.readFileSync.mockReturnValue(JSON.stringify(mockConfig));

    await configCommand({ get: 'url' });

    expect(consoleLogSpy).toHaveBeenCalledWith('http://localhost:5000');
  });

  test('should mask sensitive values when getting', async () => {
    const mockConfig = {
      apiKey: 'test-key-12345'
    };

    fs.existsSync.mockReturnValue(true);
    fs.readFileSync.mockReturnValue(JSON.stringify(mockConfig));

    await configCommand({ get: 'apiKey' });

    const output = consoleLogSpy.mock.calls[0][0];
    expect(output).not.toContain('test-key-12345');
    expect(output).toContain('*');
  });

  test('should set configuration value', async () => {
    const mockConfig = {};

    fs.existsSync.mockReturnValue(true);
    fs.readFileSync.mockReturnValue(JSON.stringify(mockConfig));
    fs.mkdirSync.mockImplementation();
    fs.writeFileSync.mockImplementation();

    await configCommand({ set: 'url=http://localhost:5000' });

    expect(fs.writeFileSync).toHaveBeenCalled();
    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('Configuration \'url\' set successfully')
    );
  });

  test('should handle invalid set format', async () => {
    await configCommand({ set: 'invalid' });

    expect(consoleErrorSpy).toHaveBeenCalled();
    expect(processExitSpy).toHaveBeenCalledWith(1);
  });

  test('should handle missing configuration key', async () => {
    fs.existsSync.mockReturnValue(true);
    fs.readFileSync.mockReturnValue(JSON.stringify({}));

    await configCommand({ get: 'nonexistent' });

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('not found')
    );
    expect(processExitSpy).toHaveBeenCalledWith(1);
  });

  test('should handle empty configuration', async () => {
    fs.existsSync.mockReturnValue(false);

    await configCommand({ list: true });

    expect(consoleLogSpy).toHaveBeenCalled();
  });
});

