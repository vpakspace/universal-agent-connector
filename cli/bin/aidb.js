#!/usr/bin/env node

/**
 * AI Agent Connector CLI Tool
 * Command-line interface for querying databases
 */

const { Command } = require('commander');
const chalk = require('chalk');
const { queryCommand } = require('../lib/commands/query');
const { explainCommand } = require('../lib/commands/explain');
const { testCommand } = require('../lib/commands/test');
const { configCommand } = require('../lib/commands/config');
const { migrateCommand } = require('../lib/commands/migrate');
const { version } = require('../package.json');

const program = new Command();

program
  .name('aidb')
  .description('CLI tool for querying databases via AI Agent Connector')
  .version(version);

// Global options
program
  .option('-u, --url <url>', 'AI Agent Connector API URL', process.env.AIDB_URL || 'http://localhost:5000')
  .option('-k, --api-key <key>', 'API key for authentication', process.env.AIDB_API_KEY)
  .option('-a, --agent-id <id>', 'Agent ID', process.env.AIDB_AGENT_ID)
  .option('-j, --json', 'Output results as JSON')
  .option('--verbose', 'Verbose output');

// Query command
program
  .command('query <question>')
  .alias('q')
  .description('Execute a natural language query')
  .option('-p, --preview', 'Preview SQL without executing')
  .option('-c, --cache', 'Use cached results if available', true)
  .option('--no-cache', 'Disable cache')
  .action(async (question, options) => {
    const globalOpts = program.opts();
    try {
      await queryCommand(question, {
        ...globalOpts,
        ...options
      });
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Explain command
program
  .command('explain <question>')
  .alias('e')
  .description('Explain what a query would do without executing it')
  .action(async (question, options) => {
    const globalOpts = program.opts();
    try {
      await explainCommand(question, {
        ...globalOpts,
        ...options
      });
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Test command
program
  .command('test')
  .description('Test connection to AI Agent Connector')
  .option('-a, --agent-id <id>', 'Agent ID to test')
  .action(async (options) => {
    const globalOpts = program.opts();
    try {
      await testCommand({
        ...globalOpts,
        ...options
      });
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Config command
program
  .command('config')
  .description('Configure CLI settings')
  .option('-s, --set <key=value>', 'Set configuration value')
  .option('-g, --get <key>', 'Get configuration value')
  .option('-l, --list', 'List all configuration')
  .action(async (options) => {
    try {
      await configCommand(options);
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Migrate command
program
  .command('migrate <action>')
  .alias('m')
  .description('Import/export configurations for environment promotion')
  .option('-o, --output <file>', 'Output file for export')
  .option('--input <file>', 'Input file for import')
  .option('--backup <file>', 'Backup file for rollback')
  .option('--validate', 'Validate only, do not import')
  .option('--dry-run', 'Show what would be done without making changes')
  .action(async (action, options) => {
    const globalOpts = program.opts();
    try {
      await migrateCommand(action, {
        ...globalOpts,
        ...options
      });
    } catch (error) {
      console.error(chalk.red('Error:'), error.message);
      process.exit(1);
    }
  });

// Parse arguments
program.parse(process.argv);

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.outputHelp();
}

