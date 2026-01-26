# Video Tutorial 2: Your First Query

**Duration**: 4 minutes  
**Target Audience**: Users who completed setup  
**Prerequisites**: Agent registered and connected

## Video Outline

### Introduction (0:00 - 0:20)

**Screen**: Show dashboard with agent ready

**Narration**:
> "Welcome back! Now that your agent is set up, let's run your first natural language query. You'll see how easy it is to query your database using plain English."

**Key Points**:
- What we'll learn
- Natural language queries
- Understanding results

---

### Step 1: Understanding Natural Language Queries (0:20 - 1:00)

**Screen**: Dashboard or API documentation

**Narration**:
> "AI Agent Connector converts your natural language questions into SQL queries automatically. Instead of writing complex SQL, you can ask questions like 'What are the top 5 products?' or 'Show me sales for last month.'"

**Screen Actions**:
1. Show example queries:
   - "What are the top 5 best-selling products?"
   - "Show me total sales for last month"
   - "How many customers do we have?"
2. Show how these convert to SQL (optional preview)
3. Explain the conversion process

**Narration**:
> "The system understands your intent and generates the appropriate SQL query. You don't need to know SQL - just ask questions naturally."

**Key Points**:
- Natural language → SQL conversion
- No SQL knowledge required
- Ask questions naturally

---

### Step 2: Running Your First Query (1:00 - 2:30)

**Screen**: Dashboard query interface or API call

**Narration**:
> "Let's run your first query. We'll use the dashboard interface, but you can also use the API or CLI tool."

**Screen Actions - Option A (Dashboard)**:
1. Navigate to agent detail page
2. Show query interface
3. Enter query: "What are the top 5 products by sales?"
4. Click "Run Query" or "Execute"
5. Show loading state
6. Show results table

**Screen Actions - Option B (API)**:
1. Show terminal/Postman
2. Show API call:
   ```bash
   curl -X POST http://localhost:5000/api/agents/my-first-agent/query/natural \
     -H "X-API-Key: <your-api-key>" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the top 5 products by sales?"}'
   ```
3. Show response with results

**Narration**:
> "Great! You got results. Notice how the system converted your question into SQL and executed it. The results show the top 5 products with their sales numbers."

**Screen Actions**:
7. Highlight the SQL that was generated (if shown)
8. Show the results table
9. Point out columns and rows

**Key Points**:
- Query executed successfully
- Results displayed in table
- SQL was generated automatically

---

### Step 3: Understanding Results (2:30 - 3:30)

**Screen**: Query results

**Narration**:
> "Let's understand what we're seeing in the results. The system returns data in a structured format with columns and rows, just like a database table."

**Screen Actions**:
1. Show results table
2. Point out:
   - Column headers
   - Data rows
   - Number of results
   - Execution time (if shown)
3. Show explanation (if available):
   - "This query shows the top 5 products ranked by total sales"
   - Statistics or insights

**Narration**:
> "You can see the product names, sales numbers, and rankings. The system also provides a natural language explanation of what the query did."

**Screen Actions**:
4. Show different result formats:
   - Table view
   - JSON view (if available)
   - Chart view (if available)

**Key Points**:
- Results are structured data
- Explanations help understand results
- Multiple view options available

---

### Step 4: Query Patterns (3:30 - 4:00)

**Screen**: Multiple query examples

**Narration**:
> "Let's try a few more query patterns to see what's possible."

**Screen Actions**:
1. Show example queries:
   - **Aggregation**: "What is the total revenue for this month?"
   - **Filtering**: "Show me customers from New York"
   - **Sorting**: "List products ordered by price"
   - **Counting**: "How many orders were placed today?"
2. Show results for each (quick examples)
3. Highlight the pattern in each query

**Narration**:
> "You can ask for aggregations, filters, sorting, and counts. The system understands these patterns and generates the right SQL."

**Key Points**:
- Various query patterns supported
- Natural language works for all
- Results are consistent

---

### Outro (4:00 - 4:15)

**Screen**: Summary screen

**Narration**:
> "Congratulations! You've run your first queries. Here's what you learned:
> - Natural language queries are easy
> - Results are displayed clearly
> - Multiple query patterns are supported
> 
> Next up: Learn how to manage permissions to control what your agents can access. See you in the next tutorial!"

**Screen Actions**:
- Show checklist
- Show link to next tutorial
- Show documentation links

**Key Points**:
- Queries are working
- Ready to learn permissions
- Next tutorial link

---

## Common Mistakes to Address

1. **Query too vague** - Show examples:
   - ❌ "Show me data"
   - ✅ "Show me sales for January 2024"
2. **No results** - Explain:
   - Query might be correct but no matching data
   - Check table names and data
3. **Permission errors** - Mention:
   - We'll cover this in next tutorial
   - Agent needs permissions to access tables
4. **Query timeout** - Explain:
   - Complex queries might take time
   - Use more specific queries

---

## Visual Elements

### Screenshots/Clips Needed

1. Query interface
2. Example queries
3. Results tables
4. SQL preview (optional)
5. Explanations
6. Different query patterns

### Text Overlays

- "Natural Language → SQL"
- "Query Pattern: Aggregation"
- "Query Pattern: Filtering"
- "Results: 5 rows"
- Key tips

### Callouts/Highlights

- Query input field
- Results table
- Important columns
- Execution time
- Explanation text

---

## Additional Resources

**Links to include:**
- [Query Documentation](../../README.md#natural-language-queries)
- [API Documentation](../../README.md#api-endpoints)
- [CLI Tool](../cli/README.md)
- [Next Tutorial: Managing Permissions](03-permissions.md)

**Example Queries to Provide:**
- List of common query patterns
- Domain-specific examples
- Best practices

---

## Production Notes

- **Pacing**: Moderate, show results clearly
- **Examples**: Use realistic data
- **Results**: Make them visible and readable
- **Zoom**: On query input and results
- **Audio**: Clear, enthusiastic tone

---

**Script Version**: 1.0  
**Last Updated**: 2024-01-15

