/**
 * TypeScript Type Definitions for Database Plugin SDK
 * 
 * These types define the interface that custom database plugins must implement.
 * Use these types when developing plugins in TypeScript/JavaScript or as
 * reference documentation for Python plugin development.
 */

/**
 * Base interface for database connector plugins
 */
export interface DatabasePlugin {
  /**
   * Unique name identifier for the plugin.
   * Should be lowercase, alphanumeric with underscores.
   * Example: 'custom_db', 'proprietary_db'
   */
  readonly pluginName: string;

  /**
   * Plugin version string (semantic versioning recommended).
   * Example: '1.0.0'
   */
  readonly pluginVersion: string;

  /**
   * Database type identifier that this plugin handles.
   * This is the value used in database_type configuration.
   * Example: 'custom_db', 'proprietary_db'
   */
  readonly databaseType: string;

  /**
   * Human-readable display name for the database.
   * Example: 'Custom Database', 'Proprietary DB'
   */
  readonly displayName: string;

  /**
   * Optional description of the plugin.
   */
  readonly description?: string;

  /**
   * Plugin author name.
   */
  readonly author?: string;

  /**
   * List of required configuration keys for this plugin.
   * These will be validated before connector creation.
   */
  readonly requiredConfigKeys: string[];

  /**
   * List of optional configuration keys for this plugin.
   */
  readonly optionalConfigKeys: string[];

  /**
   * Create a connector instance for this database type.
   * 
   * @param config - Database configuration dictionary
   * @returns Instance of the connector
   * @throws {ValueError} If required configuration is missing or invalid
   */
  createConnector(config: DatabaseConfig): DatabaseConnector;

  /**
   * Validate configuration before creating connector.
   * 
   * @param config - Configuration dictionary to validate
   * @returns Tuple of [isValid, errorMessage]
   *          If valid, returns [true, null]
   *          If invalid, returns [false, errorMessage]
   */
  validateConfig(config: DatabaseConfig): [boolean, string | null];

  /**
   * Attempt to detect if this plugin should handle the given configuration.
   * 
   * @param config - Database configuration dictionary
   * @returns Database type string if this plugin should handle it, null otherwise
   */
  detectDatabaseType(config: DatabaseConfig): string | null;

  /**
   * Get metadata about this plugin.
   * 
   * @returns Dictionary containing plugin metadata
   */
  getPluginInfo(): PluginInfo;
}

/**
 * Database configuration dictionary
 */
export interface DatabaseConfig {
  /** Database type identifier */
  type?: string;

  /** Connection string (database-specific format) */
  connection_string?: string;

  /** Database host */
  host?: string;

  /** Database port */
  port?: number;

  /** Database user */
  user?: string;

  /** Database password */
  password?: string;

  /** Database name */
  database?: string;

  /** Additional database-specific parameters */
  [key: string]: any;
}

/**
 * Base interface for database connectors
 */
export interface DatabaseConnector {
  /**
   * Establish connection to the database.
   * 
   * @returns True if connection successful
   * @throws {ConnectionError} If connection fails
   */
  connect(): boolean;

  /**
   * Close the database connection.
   * Safe to call even if not connected.
   */
  disconnect(): void;

  /**
   * Execute a query against the database.
   * 
   * @param query - Query string (SQL, MongoDB query, etc.)
   * @param params - Query parameters (optional)
   * @param fetch - Whether to fetch results (default: true)
   * @param asDict - Return results as list of dicts instead of tuples (default: false)
   * @returns Query results or null if fetch=false
   * @throws {ConnectionError} If not connected
   * @throws {Error} If query execution fails
   */
  executeQuery(
    query: string,
    params?: Record<string, any> | any[] | null,
    fetch?: boolean,
    asDict?: boolean
  ): Array<Record<string, any>> | Array<any[]> | null;

  /**
   * Check if currently connected to database.
   */
  readonly isConnected: boolean;

  /**
   * Get information about the connected database.
   * 
   * @returns Dict containing database metadata (version, name, etc.)
   */
  getDatabaseInfo(): DatabaseInfo;
}

/**
 * Database information metadata
 */
export interface DatabaseInfo {
  /** Database type */
  type: string;

  /** Database version */
  version?: string;

  /** Database name */
  name?: string;

  /** Additional metadata */
  [key: string]: any;
}

/**
 * Plugin metadata information
 */
export interface PluginInfo {
  /** Plugin name */
  name: string;

  /** Plugin version */
  version: string;

  /** Database type */
  databaseType: string;

  /** Display name */
  displayName: string;

  /** Description */
  description?: string;

  /** Author */
  author?: string;

  /** Required configuration keys */
  requiredConfigKeys: string[];

  /** Optional configuration keys */
  optionalConfigKeys: string[];
}

/**
 * Plugin registry interface
 */
export interface PluginRegistry {
  /**
   * Register a plugin instance.
   * 
   * @param plugin - Plugin instance to register
   * @returns True if registration successful, False if plugin with same name already exists
   */
  register(plugin: DatabasePlugin): boolean;

  /**
   * Unregister a plugin.
   * 
   * @param databaseType - Database type identifier
   * @returns True if unregistered, False if not found
   */
  unregister(databaseType: string): boolean;

  /**
   * Get a plugin by database type.
   * 
   * @param databaseType - Database type identifier
   * @returns Plugin instance or null if not found
   */
  getPlugin(databaseType: string): DatabasePlugin | null;

  /**
   * List all registered plugins.
   * 
   * @returns List of plugin metadata dictionaries
   */
  listPlugins(): PluginInfo[];

  /**
   * Get list of supported database types (including plugins).
   * 
   * @returns List of database type strings
   */
  getSupportedTypes(): string[];

  /**
   * Load a plugin from a Python file.
   * 
   * @param filePath - Path to the plugin Python file
   * @returns Plugin instance or null if loading failed
   */
  loadPluginFromFile(filePath: string): DatabasePlugin | null;

  /**
   * Load all plugins from a directory.
   * 
   * @param directory - Directory path containing plugin files
   * @returns List of successfully loaded plugin instances
   */
  loadPluginsFromDirectory(directory: string): DatabasePlugin[];
}

/**
 * Validation result for plugin configuration
 */
export interface ValidationResult {
  /** Whether the configuration is valid */
  isValid: boolean;

  /** Error message if invalid, null if valid */
  errorMessage: string | null;
}

/**
 * Plugin loading result
 */
export interface PluginLoadResult {
  /** Whether loading was successful */
  success: boolean;

  /** Plugin instance if successful */
  plugin?: DatabasePlugin;

  /** Error message if failed */
  error?: string;
}






