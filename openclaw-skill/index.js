/**
 * Emy-FullStack Agents Extension for OpenClaw
 * 
 * This extension allows OpenClaw to control the Emy-FullStack AI Agent System
 * through WhatsApp, Telegram, Discord, or any other connected chat channel.
 */

const EMY_API_URL = process.env.EMY_API_URL || 'http://localhost:8080';
const EMY_API_KEY = process.env.EMY_API_KEY || 'emy-openclaw-prod-key-m8n9p0';

async function fetchEmy(endpoint, options = {}) {
  const url = `${EMY_API_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': EMY_API_KEY,
    ...options.headers,
  };

  try {
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    return { error: error.message };
  }
}

// OpenClaw Extension Export
module.exports = function emyAgentsExtension(ctx) {
  return {
    name: 'emy-agents',
    description: 'Control Emy-FullStack AI Agent System',
    
    tools: {
      emy_health,
      emy_status,
      emy_agents,
      emy_command,
      emy_generate,
      emy_create_project
    }
  };
};

// Tool: emy_health
async function emy_health() {
  const result = await fetchEmy('/health');
  if (result.error) {
    return `❌ Emy-FullStack is not responding: ${result.error}`;
  }
  return `✅ **Emy-FullStack Status**
- Status: ${result.status}
- Master Brain: ${result.master_brain ? '🧠 Active' : '❌ Offline'}
- Agents Count: ${result.agents_count}
- Task Queue: ${result.task_queue ? '✅ Running' : '❌ Stopped'}`;
}

// Tool: emy_status
async function emy_status() {
  const result = await fetchEmy('/status');
  if (result.error) {
    return `❌ Could not get status: ${result.error}`;
  }
  
  let output = `📊 **Emy-FullStack Detailed Status**\n`;
  output += `- Environment: ${result.environment || 'production'}\n`;
  output += `- Uptime: ${result.uptime || 'N/A'}\n`;
  output += `- Active Tasks: ${result.active_tasks || 0}\n`;
  output += `- Pending Tasks: ${result.pending_tasks || 0}\n`;
  
  if (result.agents) {
    output += `\n**Agents:**\n`;
    for (const agent of result.agents) {
      output += `  - ${agent.name}: ${agent.status}\n`;
    }
  }
  
  return output;
}

// Tool: emy_agents
async function emy_agents() {
  const result = await fetchEmy('/agents');
  if (result.error) {
    return `❌ Could not list agents: ${result.error}`;
  }
  
  const agents = result.agents || result;
  let output = `🤖 **Available Emy Agents**\n\n`;
  
  const agentEmojis = {
    backend: '⚙️',
    frontend: '🎨',
    database: '🗄️',
    devops: '🚀',
    qa: '🧪',
    security: '🔒',
    uiux: '✨',
    aiml: '🤖',
    project_manager: '📋'
  };
  
  if (Array.isArray(agents)) {
    for (const agent of agents) {
      const emoji = agentEmojis[agent.type || agent.name] || '🔹';
      output += `${emoji} **${agent.name}**\n`;
      output += `   Status: ${agent.status || 'ready'}\n`;
      if (agent.capabilities) {
        output += `   Capabilities: ${agent.capabilities.join(', ')}\n`;
      }
      output += '\n';
    }
  } else {
    output += JSON.stringify(agents, null, 2);
  }
  
  return output;
}

// Tool: emy_command
async function emy_command({ agent, task }) {
  if (!agent || !task) {
    return '❌ Please specify both agent and task. Example: agent=backend, task="create REST API"';
  }
  
  const result = await fetchEmy('/command', {
    method: 'POST',
    body: JSON.stringify({
      agent_type: agent,
      task: task,
      priority: 'normal'
    })
  });
  
  if (result.error) {
    return `❌ Command failed: ${result.error}`;
  }
  
  return `✅ **Command Sent to ${agent}**
- Task: ${task}
- Task ID: ${result.task_id || 'N/A'}
- Status: ${result.status || 'queued'}
- Message: ${result.message || 'Task has been queued for processing'}`;
}

// Tool: emy_generate
async function emy_generate({ prompt, language = 'python' }) {
  if (!prompt) {
    return '❌ Please provide a prompt describing what code to generate.';
  }
  
  const result = await fetchEmy('/generate/code', {
    method: 'POST',
    body: JSON.stringify({
      prompt: prompt,
      language: language
    })
  });
  
  if (result.error) {
    return `❌ Code generation failed: ${result.error}`;
  }
  
  let output = `✅ **Generated ${language.toUpperCase()} Code**\n\n`;
  if (result.code) {
    output += '```' + language + '\n' + result.code + '\n```';
  } else {
    output += result.message || JSON.stringify(result, null, 2);
  }
  
  return output;
}

// Tool: emy_create_project
async function emy_create_project({ name, description, agents = '' }) {
  if (!name) {
    return '❌ Please provide a project name.';
  }
  
  const agentList = agents ? agents.split(',').map(a => a.trim()) : ['backend', 'frontend', 'database'];
  
  const result = await fetchEmy('/projects/create', {
    method: 'POST',
    body: JSON.stringify({
      name: name,
      description: description || `Project: ${name}`,
      agents: agentList
    })
  });
  
  if (result.error) {
    return `❌ Project creation failed: ${result.error}`;
  }
  
  return `✅ **Project Created**
- Name: ${name}
- ID: ${result.project_id || 'N/A'}
- Assigned Agents: ${agentList.join(', ')}
- Status: ${result.status || 'created'}`;
}
