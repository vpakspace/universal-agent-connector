# Prompt Engineering Studio Guide

Complete guide for using the Prompt Engineering Studio to customize SQL generation prompts.

## 🎯 Overview

The Prompt Engineering Studio allows power users to customize how natural language queries are converted to SQL. You can:

- **Visual Editor**: Create and edit prompts with a visual interface
- **Variables**: Use dynamic variables in your prompts
- **A/B Testing**: Compare different prompts to find the best one
- **Template Library**: Start from pre-built templates

## 🚀 Getting Started

### Accessing the Studio

1. Navigate to `/prompts` in your browser
2. Enter your agent API key
3. Start creating or editing prompts

### Quick Start

1. **Choose a Template**: Browse the template library
2. **Clone Template**: Click "Use Template" to create your own copy
3. **Customize**: Edit the prompt in the visual editor
4. **Test**: Use the preview and test features
5. **Activate**: Set status to "Active" when ready

## 📝 Creating Prompts

### Basic Prompt Structure

A prompt consists of:

1. **System Prompt**: Instructions for the AI model
2. **User Prompt Template**: Template for the user's query
3. **Variables**: Dynamic values that get replaced

### Example Prompt

**System Prompt:**
```
You are a SQL expert specializing in {{database_type}} databases.
Your task is to convert natural language questions into accurate SQL queries.

Rules:
1. Generate ONLY valid {{database_type}} SQL
2. Use proper table and column names from the schema
3. Return ONLY the SQL query, no explanations

Schema Information:
{{schema_info}}
```

**User Prompt Template:**
```
{{natural_language_query}}
```

### Variables

Variables are placeholders that get replaced with actual values:

- `{{database_type}}` - Database type (PostgreSQL, MySQL, etc.)
- `{{schema_info}}` - Formatted schema information
- `{{natural_language_query}}` - The user's natural language query
- Custom variables you define

### Defining Variables

In the editor:

1. Click "+ Add Variable"
2. Enter variable name (e.g., `max_results`)
3. Add description
4. Set default value
5. Mark as required if needed

Use in prompts: `{{max_results}}`

## 🎨 Visual Editor

### Features

- **Live Preview**: See how your prompt renders in real-time
- **Variable Management**: Add, edit, and remove variables
- **Syntax Highlighting**: Better readability
- **Test Mode**: Test with sample queries

### Editor Layout

- **Left Panel**: Prompt configuration
  - Name and description
  - System prompt editor
  - User prompt template
  - Variables section
  - Status selector

- **Right Panel**: Preview
  - Rendered system prompt
  - Rendered user prompt
  - Test query input

### Tips

- Use clear, specific instructions
- Include schema information in system prompt
- Test with various query types
- Keep prompts focused and concise

## 🧪 A/B Testing

### Creating an A/B Test

1. Create two different prompts (A and B)
2. Go to A/B Testing tab
3. Click "Create A/B Test"
4. Select prompt A and prompt B
5. Set split ratio (default: 50/50)
6. Activate the test

### How It Works

- Queries are randomly assigned to prompt A or B
- Metrics are tracked for each prompt:
  - Query count
  - Success rate
  - Error rate
  - Average tokens used

### Viewing Results

1. Go to A/B Testing tab
2. Click "View Results" on a test
3. Compare metrics:
  - Which prompt has higher success rate?
  - Which uses fewer tokens?
  - Which generates better SQL?

### Best Practices

- Test with real queries
- Run tests for sufficient time
- Monitor both prompts
- Document findings

## 📚 Template Library

### Available Templates

1. **PostgreSQL Default**
   - Standard prompt for PostgreSQL
   - Good starting point
   - Balanced approach

2. **Analytics Optimized**
   - Optimized for analytical queries
   - Focuses on aggregations
   - Good for reporting

3. **Strict Validation**
   - Strict validation rules
   - Explicit JOIN syntax
   - No SELECT *

### Using Templates

1. Browse templates
2. Click "Use Template"
3. Enter a name for your prompt
4. Customize as needed
5. Save and activate

### Creating Custom Templates

1. Create a prompt
2. Test thoroughly
3. Mark as template (in metadata)
4. Share with team

## 🔧 Advanced Features

### Custom Variables

Define your own variables:

```
Variable: max_rows
Description: Maximum number of rows to return
Default: 100
```

Use in prompt:
```
Limit results to {{max_rows}} rows maximum.
```

### Prompt Metadata

Add metadata for organization:

```json
{
  "category": "analytics",
  "optimized_for": "reporting",
  "database_type": "postgresql"
}
```

### Prompt Status

- **Draft**: Work in progress
- **Active**: Currently in use
- **Testing**: Being tested
- **Archived**: No longer used

## 📊 Integration

### Using Custom Prompts

In API requests, include `prompt_id`:

```json
{
  "query": "Show me all users",
  "prompt_id": "prompt-abc123"
}
```

### Programmatic Access

```python
import requests

response = requests.post(
    'http://localhost:5000/api/agents/my-agent/query/natural',
    headers={'X-API-Key': 'your-api-key'},
    json={
        'query': 'Show me all users',
        'prompt_id': 'prompt-abc123'
    }
)
```

## 🎯 Best Practices

### Prompt Design

1. **Be Specific**: Clear instructions work better
2. **Include Context**: Schema information helps
3. **Set Rules**: Define constraints clearly
4. **Test Thoroughly**: Try various query types
5. **Iterate**: Refine based on results

### Variable Usage

1. **Use Defaults**: Provide sensible defaults
2. **Document Variables**: Clear descriptions
3. **Required vs Optional**: Mark appropriately
4. **Naming**: Use clear, descriptive names

### A/B Testing

1. **One Variable**: Change one thing at a time
2. **Sufficient Sample**: Test with enough queries
3. **Real Data**: Use actual queries
4. **Monitor Closely**: Watch for issues
5. **Document Results**: Keep notes

## 🐛 Troubleshooting

### Prompt Not Working

- Check variable names match
- Verify syntax (double curly braces)
- Test with simple query first
- Check prompt status

### Variables Not Replacing

- Ensure variable names match exactly
- Check variable is defined
- Verify default values
- Test in preview

### A/B Test Not Running

- Check test status is "active"
- Verify both prompts exist
- Check agent ID matches
- Review API logs

## 📚 Examples

### Example 1: Analytics Prompt

**System Prompt:**
```
You are a SQL expert for {{database_type}} analytics queries.
Focus on generating efficient queries for reporting.

Rules:
1. Prefer aggregations (SUM, COUNT, AVG)
2. Use GROUP BY for grouping
3. Include ORDER BY for sorted results
4. Optimize for read performance

Schema:
{{schema_info}}
```

### Example 2: Strict Validation Prompt

**System Prompt:**
```
You are a SQL expert with strict validation for {{database_type}}.

Rules:
1. Validate all table/column names against schema
2. Use explicit JOIN syntax
3. Always specify column names (no SELECT *)
4. Include WHERE clauses for filtering
5. Validate data types

Schema:
{{schema_info}}
```

## 🔗 Related Documentation

- [API Documentation](../README.md#api)
- [Natural Language Queries](../README.md#natural-language-queries)
- [Contributing Guide](../CONTRIBUTING.md)

---

**Questions?** Check [GitHub Discussions](https://github.com/your-repo/ai-agent-connector/discussions) or open an issue!

