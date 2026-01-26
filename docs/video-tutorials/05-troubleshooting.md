# Video Tutorial 5: Troubleshooting Common Issues

**Duration**: 6 minutes  
**Target Audience**: Users encountering problems  
**Prerequisites**: Basic familiarity with the system

## Video Outline

### Introduction (0:00 - 0:25)

**Screen**: Common error messages collage

**Narration**:
> "Even with the best setup, you'll occasionally encounter issues. In this tutorial, we'll cover the most common problems and how to fix them quickly. By the end, you'll be able to troubleshoot most issues on your own."

**Key Points**:
- Common issues we'll cover
- Troubleshooting mindset
- When to get help

---

### Issue 1: Connection Problems (0:25 - 1:30)

**Screen**: Connection error messages

**Narration**:
> "Let's start with connection problems. These are the most common issues when setting up agents."

**Screen Actions**:
1. Show connection error:
   - "Failed to connect to database"
   - "Connection timeout"
   - "Invalid credentials"
2. Show troubleshooting steps:
   - **Check database is running**: Show how to verify
   - **Verify credentials**: Show connection string format
   - **Check network**: Show how to test connectivity
   - **Check firewall**: Mention firewall rules
   - **Test connection**: Use test endpoint
3. Show test connection command:
   ```bash
   curl -X POST http://localhost:5000/api/databases/test \
     -H "Content-Type: application/json" \
     -d '{"connection_string": "postgresql://..."}'
   ```
4. Show successful connection

**Narration**:
> "Most connection issues are due to incorrect credentials, the database not running, or network problems. Always test the connection before registering an agent."

**Key Points**:
- Test connection first
- Verify credentials
- Check database status
- Network issues common

---

### Issue 2: Permission Errors (1:30 - 2:30)

**Screen**: Permission error messages

**Narration**:
> "Permission errors are common when agents try to access tables they don't have permission for. Let's see how to fix these."

**Screen Actions**:
1. Show permission error:
   - "Permission denied: agent does not have access to table 'products'"
   - "Access denied for resource: customers"
2. Show how to identify the issue:
   - Read the error message carefully
   - Identify which table/resource
   - Check current permissions
3. Show how to fix:
   - Go to agent permissions
   - Grant missing permission
   - Re-run query
4. Show access preview (if available):
   - Visual representation
   - See what's missing
5. Show successful query after fix

**Narration**:
> "Permission errors are easy to fix once you understand them. The error message tells you exactly what's missing. Just grant the permission and try again."

**Screen Actions**:
6. Show common permission mistakes:
   - Forgot to grant permissions
   - Wrong permission type (read vs write)
   - Permissions on wrong resource

**Key Points**:
- Error messages are helpful
- Easy to fix
- Use access preview
- Check permissions first

---

### Issue 3: Query Failures (2:30 - 3:45)

**Screen**: Query error messages

**Narration**:
> "Query failures can happen for various reasons. Let's look at the most common causes and how to fix them."

**Screen Actions**:
1. Show different error types:
   - **SQL Syntax Errors**: "Invalid SQL syntax"
   - **Table Not Found**: "Table 'xyz' does not exist"
   - **Column Not Found**: "Column 'abc' does not exist"
   - **Timeout Errors**: "Query execution timeout"
   - **NL Conversion Errors**: "Could not convert to SQL"
2. For each error type, show:
   - What the error means
   - Common causes
   - How to fix
3. Show debugging steps:
   - Check the generated SQL
   - Verify table/column names
   - Check query complexity
   - Review query logs
4. Show SQL preview:
   - Use `--preview` flag or preview mode
   - Review SQL before executing
   - Fix issues in natural language query

**Narration**:
> "Most query failures are due to table/column name mismatches, overly complex queries, or timeouts. Use the SQL preview to see what SQL is being generated, and simplify your query if needed."

**Screen Actions**:
5. Show query optimization tips:
   - Be more specific
   - Break down complex queries
   - Use correct table/column names
   - Add filters to reduce data

**Key Points**:
- Multiple error types
- SQL preview helps
- Simplify queries
- Check table/column names

---

### Issue 4: Performance Issues (3:45 - 4:45)

**Screen**: Slow query indicators

**Narration**:
> "Slow queries can be frustrating. Let's see how to identify and fix performance issues."

**Screen Actions**:
1. Show performance indicators:
   - Query taking too long
   - Timeout errors
   - High execution times in logs
2. Show how to identify slow queries:
   - Check execution time in logs
   - Look for timeout errors
   - Review performance dashboard
3. Show optimization strategies:
   - **Simplify queries**: Break down complex queries
   - **Add filters**: Reduce data scanned
   - **Use indexes**: Mention database indexes
   - **Enable caching**: Use query caching
   - **Optimize database**: Database-level optimizations
4. Show query tracing (if available):
   - See where time is spent
   - Identify bottlenecks
5. Show before/after:
   - Slow query example
   - Optimized version
   - Performance improvement

**Narration**:
> "Performance issues are often due to complex queries or missing database indexes. Simplify your queries, add appropriate filters, and work with your DBA to optimize the database if needed."

**Key Points**:
- Identify slow queries
- Simplify and optimize
- Use caching
- Database optimization

---

### Issue 5: Getting Help (4:45 - 5:30)

**Screen**: Help resources

**Narration**:
> "Sometimes you need additional help. Let's see what resources are available."

**Screen Actions**:
1. Show help resources:
   - **Documentation**: Link to docs
   - **Error messages**: Often contain solutions
   - **Logs**: Detailed error information
   - **Community**: Forums, Discord, etc.
   - **Support**: Contact information
2. Show how to gather information for support:
   - Error messages
   - Query logs
   - Configuration (sanitized)
   - Steps to reproduce
3. Show debugging checklist:
   - Check error messages
   - Review logs
   - Test with simple query
   - Verify permissions
   - Check connection
4. Show common solutions summary:
   - Connection issues → Test connection
   - Permission errors → Grant permissions
   - Query failures → Check SQL, simplify
   - Performance → Optimize queries

**Narration**:
> "Before asking for help, gather as much information as possible: error messages, logs, and steps to reproduce. This helps others help you faster."

**Key Points**:
- Multiple help resources
- Gather information first
- Use debugging checklist
- Community support available

---

### Issue 6: Quick Reference (5:30 - 6:00)

**Screen**: Troubleshooting quick reference

**Narration**:
> "Let's create a quick reference guide for common issues and solutions."

**Screen Actions**:
1. Show quick reference table:
   - **Issue** | **Quick Fix**
   - Connection failed → Test connection, check credentials
   - Permission denied → Grant permissions
   - Query failed → Check SQL, simplify query
   - Slow query → Optimize, add filters
   - Timeout → Simplify query, check database
2. Show debugging workflow:
   - Read error message
   - Check logs
   - Verify configuration
   - Test with simple case
   - Escalate if needed
3. Show prevention tips:
   - Test connections first
   - Grant permissions proactively
   - Start with simple queries
   - Monitor performance
   - Review logs regularly

**Narration**:
> "Keep this quick reference handy. Most issues follow these patterns, and the solutions are usually straightforward."

**Key Points**:
- Quick reference available
- Common patterns
- Prevention is key

---

### Outro (6:00 - 6:15)

**Screen**: Summary screen

**Narration**:
> "Excellent! You're now equipped to troubleshoot common issues. Here's what we covered:
> - Connection problems
> - Permission errors
> - Query failures
> - Performance issues
> - Getting help
> - Quick reference
> 
> Remember: most issues have simple solutions. Read error messages carefully, check logs, and use the resources available. Happy querying!"

**Screen Actions**:
- Show troubleshooting checklist
- Show help resources
- Show documentation links
- Show community links

**Key Points**:
- Troubleshooting skills learned
- Resources available
- Most issues are solvable

---

## Common Issues Summary

### Quick Fix Guide

| Issue | Symptom | Quick Fix |
|-------|---------|-----------|
| Connection Failed | "Failed to connect" | Test connection, check credentials |
| Permission Denied | "Access denied" | Grant permissions to resource |
| Query Failed | "Invalid SQL" | Check SQL, simplify query |
| Slow Query | Long execution time | Optimize, add filters, use cache |
| Timeout | "Query timeout" | Simplify query, check database |
| Table Not Found | "Table does not exist" | Check table name, verify permissions |
| Column Not Found | "Column does not exist" | Check column name, verify schema |

---

## Visual Elements

### Screenshots/Clips Needed

1. Connection error messages
2. Permission error messages
3. Query error messages
4. Performance indicators
5. Help resources
6. Quick reference guide
7. Debugging workflow

### Text Overlays

- "Issue: Connection Failed"
- "Solution: Test Connection"
- "Quick Fix"
- "Debugging Steps"
- "Help Resources"
- Key troubleshooting tips

### Callouts/Highlights

- Error messages
- Solution steps
- Help links
- Quick fixes
- Prevention tips

---

## Additional Resources

**Links to include:**
- [Troubleshooting Guide](../../README.md#troubleshooting)
- [Error Reference](../../README.md#errors)
- [Support Documentation](../../README.md#support)
- [Community Forums](link-to-forums)
- [API Documentation](../../README.md#api-endpoints)

**Troubleshooting Resources:**
- Common errors and solutions
- Debugging checklist
- Performance optimization guide
- Support contact information

---

## Production Notes

- **Pacing**: Clear, problem-solving focused
- **Examples**: Real error messages
- **Solutions**: Step-by-step, actionable
- **Tone**: Helpful, reassuring
- **Audio**: Patient, instructional tone

---

**Script Version**: 1.0  
**Last Updated**: 2024-01-15

