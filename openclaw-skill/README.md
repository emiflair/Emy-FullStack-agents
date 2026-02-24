# Emy-Agents Skill for OpenClaw

This OpenClaw skill allows you to control the Emy-FullStack AI Agent System through WhatsApp, Telegram, Discord, or any other chat channel connected to OpenClaw.

## Available Commands

Once installed, you can use natural language to interact with your agents:

### Health Check
> "Check if Emy is running"
> "Is the agent system healthy?"

### Status
> "What's the status of my agents?"
> "Show me the current system status"

### List Agents
> "What agents do I have?"
> "List all available agents"

### Send Commands
> "Tell the backend agent to create a REST API for users"
> "Ask frontend to build a login page"
> "Have devops set up CI/CD pipeline"

### Generate Code
> "Generate a Python function to sort a list"
> "Create a TypeScript interface for user data"

### Create Projects
> "Create a new project called MyApp with backend and frontend agents"

## Installation

1. Copy the `openclaw-skill` folder to `~/.openclaw/skills/emy-agents/` on your server
2. Restart OpenClaw gateway: `systemctl restart openclaw`
3. The skill will be automatically loaded

## Environment Variables

- `EMY_API_URL` - URL of your Emy-FullStack API (default: http://localhost:8080)
- `EMY_API_KEY` - API key for authentication

## Supported Agents

- **backend** - Backend development (APIs, databases, server logic)
- **frontend** - Frontend development (UI, React, Vue, etc.)
- **database** - Database design and queries
- **devops** - CI/CD, Docker, deployment
- **qa** - Testing and quality assurance
- **security** - Security audits and best practices
- **uiux** - UI/UX design recommendations
- **aiml** - AI/ML model development
- **project_manager** - Project coordination
