# Video Tutorial 3: Managing Permissions

**Duration**: 6 minutes  
**Target Audience**: Users who want to control access  
**Prerequisites**: Agent registered, first query completed

## Video Outline

### Introduction (0:00 - 0:25)

**Screen**: Show permission error or agent detail page

**Narration**:
> "In this tutorial, we'll learn how to manage permissions for your agents. Permissions control what tables and data your agents can access, which is crucial for security and data governance."

**Key Points**:
- Why permissions matter
- What we'll cover
- Security importance

---

### Step 1: Understanding Permissions (0:25 - 1:15)

**Screen**: Permission concepts diagram

**Narration**:
> "Permissions in AI Agent Connector work at two levels: general permissions and resource-level permissions. General permissions control what actions an agent can perform, while resource-level permissions control access to specific tables, columns, or databases."

**Screen Actions**:
1. Show permission hierarchy:
   - Agent level
   - Resource level (tables, columns)
2. Show permission types:
   - `read` - Can query data
   - `write` - Can modify data
   - `admin` - Full access
3. Show example:
   - Agent has `read` on `products` table
   - Agent has `read` and `write` on `orders` table
   - Agent has no access to `users` table

**Narration**:
> "By default, agents have no permissions. You need to explicitly grant access to resources. This follows the principle of least privilege - agents only get access to what they need."

**Key Points**:
- Two-level permission system
- Explicit permissions required
- Principle of least privilege

---

### Step 2: Viewing Current Permissions (1:15 - 2:00)

**Screen**: Agent detail page or permissions view

**Narration**:
> "Let's see what permissions your agent currently has. Navigate to your agent's detail page."

**Screen Actions**:
1. Go to Agents page
2. Click on an agent
3. Show permissions section
4. Show current permissions (likely empty for new agent)
5. Show "Access Preview" if available
6. Explain what each section means

**Narration**:
> "As you can see, this agent has no permissions yet. That's why queries might fail with permission errors. Let's fix that by granting some permissions."

**Screen Actions**:
7. Show permission error example (if applicable)
8. Explain the error message

**Key Points**:
- Check permissions before querying
- Empty permissions = no access
- Permission errors are clear

---

### Step 3: Granting Permissions via Dashboard (2:00 - 3:30)

**Screen**: Permission management interface

**Narration**:
> "There are two ways to grant permissions: using the dashboard or the API. Let's start with the dashboard, which is easier for beginners."

**Screen Actions - Method 1 (Dashboard UI)**:
1. Show "Set Permissions" or "Manage Access" button
2. Click to open permission dialog
3. Show available tables list
4. Select a table (e.g., "products")
5. Select permissions: `read`
6. Click "Grant Permission"
7. Show success message
8. Show updated permissions list

**Screen Actions - Method 2 (API)**:
1. Show API call:
   ```bash
   curl -X PUT http://localhost:5000/api/agents/my-agent/permissions/resources \
     -H "X-API-Key: <your-api-key>" \
     -H "Content-Type: application/json" \
     -d '{
       "resource_id": "products",
       "resource_type": "table",
       "permissions": ["read"]
     }'
   ```
2. Show response
3. Explain the API format

**Narration**:
> "Great! Now your agent has read access to the products table. Let's grant permissions to a few more tables."

**Screen Actions**:
9. Grant permissions to multiple tables:
   - `customers` - read
   - `orders` - read, write
   - `order_items` - read
10. Show all permissions in list

**Key Points**:
- Dashboard is easiest for beginners
- API is better for automation
- Can grant multiple permissions

---

### Step 4: Permission Best Practices (3:30 - 4:45)

**Screen**: Best practices checklist

**Narration**:
> "Let's talk about permission best practices to keep your data secure."

**Screen Actions**:
1. Show best practices:
   - **Principle of Least Privilege**: Only grant what's needed
   - **Read-Only for Analytics**: Analytics agents usually only need read
   - **Separate Agents**: Different agents for different purposes
   - **Regular Audits**: Review permissions periodically
   - **Document Permissions**: Keep track of what's granted
2. Show example scenarios:
   - Analytics agent: read-only on reporting tables
   - ETL agent: read and write on staging tables
   - Admin agent: full access (use sparingly)

**Narration**:
> "For most use cases, agents only need read permissions. Only grant write permissions if the agent needs to modify data. And always use separate agents for different purposes - don't give one agent access to everything."

**Screen Actions**:
3. Show permission audit view (if available)
4. Show how to review all permissions
5. Show how to revoke permissions

**Key Points**:
- Least privilege principle
- Read-only for most cases
- Regular audits important
- Document everything

---

### Step 5: Testing Permissions (4:45 - 5:30)

**Screen**: Running queries with permissions

**Narration**:
> "Let's test that our permissions are working correctly. We'll run queries that should work and ones that should fail."

**Screen Actions**:
1. Run query on permitted table:
   - "Show me products"
   - Show successful results
2. Run query on non-permitted table:
   - "Show me users"
   - Show permission error
3. Explain the error message
4. Show how to grant the missing permission
5. Re-run query and show success

**Narration**:
> "Perfect! The permission system is working. Queries on permitted tables succeed, while queries on non-permitted tables fail with clear error messages."

**Key Points**:
- Permissions are enforced
- Error messages are helpful
- Easy to fix missing permissions

---

### Step 6: Access Preview (5:30 - 6:00)

**Screen**: Access preview feature

**Narration**:
> "AI Agent Connector includes an access preview feature that shows exactly what an agent can access. This is great for transparency and troubleshooting."

**Screen Actions**:
1. Navigate to access preview (if available)
2. Show visual representation:
   - Tables agent can access (green)
   - Tables agent cannot access (red/gray)
   - Permissions for each table
3. Show column-level permissions (if applicable)
4. Explain how to use this for troubleshooting

**Narration**:
> "The access preview gives you a clear visual of what your agent can and cannot access. Use this to verify permissions and troubleshoot query issues."

**Key Points**:
- Visual permission overview
- Great for troubleshooting
- Self-service transparency

---

### Outro (6:00 - 6:15)

**Screen**: Summary screen

**Narration**:
> "Excellent! You now understand how to manage permissions. Here's what we covered:
> - Understanding permission levels
> - Granting permissions via dashboard and API
> - Best practices for security
> - Testing permissions
> - Using access preview
> 
> Next up: Learn how to monitor your agents and track usage. See you in the next tutorial!"

**Screen Actions**:
- Show checklist
- Show link to next tutorial
- Show security documentation link

**Key Points**:
- Permissions are essential
- Security best practices
- Next tutorial link

---

## Common Mistakes to Address

1. **Granting too many permissions** - Emphasize least privilege
2. **Forgetting to grant permissions** - Show how to check
3. **Granting write when read is enough** - Explain the difference
4. **Not documenting permissions** - Show documentation importance
5. **Permission errors not understood** - Show how to read error messages

---

## Visual Elements

### Screenshots/Clips Needed

1. Permission hierarchy diagram
2. Agent permissions view
3. Permission grant dialog
4. Permission list
5. Permission errors
6. Access preview
7. Best practices checklist

### Text Overlays

- "Permission Level: Resource"
- "Permission Type: Read"
- "Principle of Least Privilege"
- "Access Granted"
- "Permission Denied"
- Key security tips

### Callouts/Highlights

- Permission checkboxes
- Resource lists
- Error messages
- Access preview colors
- Security warnings

---

## Additional Resources

**Links to include:**
- [Permission Documentation](../../README.md#access-control)
- [Security Guide](../../SECURITY.md)
- [API Documentation](../../README.md#api-endpoints)
- [Next Tutorial: Monitoring & Analytics](04-monitoring.md)

**Security Resources:**
- Permission best practices
- Security checklist
- Audit guidelines

---

## Production Notes

- **Pacing**: Clear and methodical
- **Security**: Emphasize importance
- **Examples**: Use realistic scenarios
- **Warnings**: Highlight security concerns
- **Audio**: Professional, security-focused tone

---

**Script Version**: 1.0  
**Last Updated**: 2024-01-15

