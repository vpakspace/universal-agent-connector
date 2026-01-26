# Video Tutorial 1: Getting Started - Setup & Installation

**Duration**: 5 minutes  
**Target Audience**: Complete beginners  
**Prerequisites**: None

## Video Outline

### Introduction (0:00 - 0:30)

**Screen**: Show AI Agent Connector logo and title screen

**Narration**:
> "Welcome to AI Agent Connector! In this first tutorial, we'll get you set up and running in just 5 minutes. By the end, you'll have your first agent connected and ready to query your database."

**Key Points**:
- What we'll accomplish
- What you'll need (database, API key)
- Time commitment

---

### Step 1: Installation (0:30 - 1:30)

**Screen**: Terminal/command line

**Narration**:
> "First, let's install AI Agent Connector. You can run it locally or use our browser-based playground. For this tutorial, we'll use the local installation."

**Screen Actions**:
1. Show terminal
2. Create virtual environment: `python -m venv venv`
3. Activate: `source venv/bin/activate` (or `.\\venv\\Scripts\\Activate.ps1` on Windows)
4. Install: `pip install -r requirements.txt`
5. Show successful installation

**Narration**:
> "Great! The installation is complete. Now let's start the server."

**Screen Actions**:
6. Start server: `python main.py`
7. Show server starting message
8. Highlight the dashboard URL: `http://localhost:5000/dashboard`

**Key Points**:
- Virtual environment is recommended
- Server runs on port 5000 by default
- Dashboard is available immediately

---

### Step 2: Access the Dashboard (1:30 - 2:00)

**Screen**: Browser showing dashboard

**Narration**:
> "Open your browser and navigate to the dashboard. You'll see the main interface with options to register agents, view existing agents, and access the integration wizard."

**Screen Actions**:
1. Open browser
2. Navigate to `http://localhost:5000/dashboard`
3. Show dashboard overview
4. Point out key sections:
   - Agent management
   - Integration wizard
   - System status

**Key Points**:
- Dashboard is the main interface
- No coding required
- Wizard guides you through setup

---

### Step 3: Register Your First Agent (2:00 - 3:30)

**Screen**: Integration wizard

**Narration**:
> "Let's register your first agent. Click on 'New Integration' or 'Wizard' to start. The wizard will guide you through three simple steps."

**Screen Actions**:
1. Click "New Integration" or "Wizard"
2. Show Step 1: Agent Information
   - Enter agent ID: `my-first-agent`
   - Enter agent name: `My First Agent`
   - Select agent type: `analytics`
3. Show Step 2: Database Connection
   - Enter connection string: `postgresql://user:pass@localhost:5432/mydb`
   - Click "Test Connection"
   - Show success message
4. Show Step 3: Review & Connect
   - Review configuration
   - Click "Register Agent"
   - Show success message with API key

**Narration**:
> "Perfect! Your agent is registered. Save the API key - you'll need it for queries. Notice that the connection string is encrypted for security."

**Key Points**:
- Agent ID must be unique
- Test connection before registering
- Save API key securely
- Connection strings are encrypted

---

### Step 4: Verify Setup (3:30 - 4:30)

**Screen**: Agent detail page

**Narration**:
> "Let's verify everything is set up correctly. Go to the Agents page and click on your agent."

**Screen Actions**:
1. Navigate to Agents page
2. Click on "my-first-agent"
3. Show agent details:
   - Agent information
   - Database connection status
   - Permissions (empty for now)
4. Show "Test Connection" button
5. Click it and show success

**Narration**:
> "Excellent! Your agent is connected and ready. In the next tutorial, we'll run your first query."

**Key Points**:
- Agent is registered and connected
- Database connection is verified
- Ready for queries

---

### Step 5: Quick Test (4:30 - 5:00)

**Screen**: API test or dashboard query

**Narration**:
> "Let's do a quick test to make sure everything works. We'll use the dashboard to test a simple query."

**Screen Actions**:
1. Show query interface (if available in dashboard)
2. Or show API test with curl:
   ```bash
   curl -X POST http://localhost:5000/api/agents/my-first-agent/query/natural \
     -H "X-API-Key: <your-api-key>" \
     -H "Content-Type: application/json" \
     -d '{"query": "How many tables are in the database?"}'
   ```
3. Show successful response

**Narration**:
> "Perfect! Everything is working. In the next video, we'll learn how to write effective queries."

---

### Outro (5:00 - 5:15)

**Screen**: Summary screen with key points

**Narration**:
> "You've successfully set up AI Agent Connector! Here's what we accomplished:
> - Installed the application
> - Started the server
> - Registered your first agent
> - Connected to your database
> - Verified everything works
> 
> Next up: Learn how to write your first query. See you in the next tutorial!"

**Screen Actions**:
- Show checklist of completed steps
- Show link to next tutorial
- Show documentation links

**Key Points**:
- Setup complete
- Ready for queries
- Next tutorial link

---

## Common Mistakes to Address

1. **Wrong Python version** - Show how to check: `python --version`
2. **Port already in use** - Show how to change port: `export PORT=5001`
3. **Database connection fails** - Show common issues:
   - Wrong credentials
   - Database not running
   - Network issues
4. **API key not saved** - Emphasize saving it
5. **Virtual environment not activated** - Show activation step clearly

---

## Visual Elements

### Screenshots/Clips Needed

1. Terminal showing installation
2. Dashboard home page
3. Integration wizard (all steps)
4. Agent detail page
5. Success messages
6. Error messages (for troubleshooting)

### Text Overlays

- "Step 1: Installation"
- "Step 2: Access Dashboard"
- "Step 3: Register Agent"
- "Step 4: Verify Setup"
- "Step 5: Quick Test"
- Key tips and warnings

### Callouts/Highlights

- API key (highlight and emphasize)
- Connection string format
- Success indicators
- Error messages
- Important buttons

---

## Additional Resources

**Links to include in video description:**
- [Installation Guide](../../README.md#installation)
- [Dashboard Documentation](../../README.md#web-dashboard)
- [API Documentation](../../README.md#api-endpoints)
- [Next Tutorial: Your First Query](02-first-query.md)

**Code snippets to provide:**
- Installation commands
- Connection string examples
- API test commands

---

## Production Notes

- **Pacing**: Slow and clear for beginners
- **Pauses**: After each major step
- **Zoom**: On important UI elements
- **Cursor**: Highlight clicks and interactions
- **Audio**: Clear narration, minimal background noise

---

**Script Version**: 1.0  
**Last Updated**: 2024-01-15

