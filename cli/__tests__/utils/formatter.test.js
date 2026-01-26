/**
 * Tests for output formatter
 */

const { formatOutput } = require('../../lib/utils/formatter');

describe('Output Formatter', () => {
  let consoleLogSpy;

  beforeEach(() => {
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('should format preview results', () => {
    const result = {
      sql: 'SELECT * FROM products',
      explanation: 'Retrieves all products',
      tables_used: ['products'],
      columns_used: ['id', 'name']
    };

    formatOutput(result, { preview: true });

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('Generated SQL')
    );
    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('SELECT * FROM products')
    );
  });

  test('should format query results with rows', () => {
    const result = {
      sql: 'SELECT * FROM products LIMIT 2',
      rows: [
        { id: 1, name: 'Product 1', price: 100 },
        { id: 2, name: 'Product 2', price: 200 }
      ],
      columns: ['id', 'name', 'price'],
      execution_time: 45
    };

    formatOutput(result, { preview: false });

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('Results')
    );
    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('2 row(s)')
    );
  });

  test('should format empty results', () => {
    const result = {
      sql: 'SELECT * FROM products WHERE id = 999',
      rows: [],
      columns: ['id', 'name', 'price']
    };

    formatOutput(result, { preview: false });

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('No results found')
    );
  });

  test('should show SQL in verbose mode', () => {
    const result = {
      sql: 'SELECT * FROM products',
      rows: [{ id: 1, name: 'Product 1' }],
      columns: ['id', 'name']
    };

    formatOutput(result, { preview: false, verbose: true });

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('Executed SQL')
    );
  });

  test('should format results with explanation', () => {
    const result = {
      rows: [{ id: 1, name: 'Product 1' }],
      columns: ['id', 'name'],
      explanation: 'This query shows all products'
    };

    formatOutput(result, { preview: false });

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('Explanation')
    );
  });

  test('should format results with statistics', () => {
    const result = {
      rows: [{ id: 1, name: 'Product 1' }],
      columns: ['id', 'name'],
      statistics: {
        total_rows: 1,
        execution_time: 45
      }
    };

    formatOutput(result, { preview: false });

    expect(consoleLogSpy).toHaveBeenCalledWith(
      expect.stringContaining('Statistics')
    );
  });

  test('should handle null values', () => {
    const result = {
      rows: [
        { id: 1, name: 'Product 1', price: null },
        { id: 2, name: null, price: 200 }
      ],
      columns: ['id', 'name', 'price']
    };

    formatOutput(result, { preview: false });

    expect(consoleLogSpy).toHaveBeenCalled();
  });

  test('should handle missing columns', () => {
    const result = {
      rows: [
        { id: 1, name: 'Product 1' },
        { id: 2, name: 'Product 2' }
      ]
    };

    formatOutput(result, { preview: false });

    expect(consoleLogSpy).toHaveBeenCalled();
  });
});

