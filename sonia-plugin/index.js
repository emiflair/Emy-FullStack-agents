/**
 * Sonia AI Assistant Plugin for OpenClaw
 * 
 * Autonomous AI assistant with capabilities for:
 * - Email (send/receive via Zoho)
 * - Browser automation (account creation, web interaction)
 * - Social media posting and engagement
 * - Task completion and reporting
 */

const { execSync } = require('child_process');
const fs = require('fs');

// Configuration
const CONFIG = {
  email: 'sonia@wazhop.com',
  name: 'Sonia Wazhop',
  whatsapp_default: '+971551994544',
  browser_profile: 'server',
  work_dir: '/opt/emy-fullstack/sonia-workspace'
};

// Ensure workspace directory exists
try {
  if (!fs.existsSync(CONFIG.work_dir)) {
    fs.mkdirSync(CONFIG.work_dir, { recursive: true });
  }
} catch (e) {}

/**
 * Execute shell command and return output
 */
function runCommand(cmd, timeout = 30000) {
  try {
    const result = execSync(cmd, {
      encoding: 'utf8',
      timeout: timeout,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return { success: true, output: (result || '').trim() };
  } catch (error) {
    return { success: false, error: error.message, stderr: error.stderr?.toString() || '' };
  }
}

/**
 * Send email using msmtp
 */
async function sonia_send_email({ to, subject, body, cc }) {
  if (!to || !subject || !body) {
    return '❌ Missing required fields: to, subject, and body are required';
  }
  
  const headers = [
    `To: ${to}`,
    `From: ${CONFIG.name} <${CONFIG.email}>`,
    `Subject: ${subject}`,
    cc ? `Cc: ${cc}` : '',
    'Content-Type: text/plain; charset=UTF-8',
    '',
    body
  ].filter(Boolean).join('\n');

  const tmpFile = `/tmp/sonia_email_${Date.now()}.txt`;
  fs.writeFileSync(tmpFile, headers);

  const result = runCommand(`cat ${tmpFile} | msmtp -t`);
  try { fs.unlinkSync(tmpFile); } catch(e) {}

  if (result.success) {
    return `✅ **Email Sent**
- From: ${CONFIG.email}
- To: ${to}
- Subject: ${subject}`;
  }
  return `❌ Failed to send email: ${result.error}`;
}

/**
 * Check incoming emails using IMAP
 */
async function sonia_check_email({ folder, limit, unread_only }) {
  const folderName = folder || 'INBOX';
  const unreadFlag = unread_only !== false ? 'UNSEEN' : 'ALL';
  
  // Use fetchmail to check emails
  const fetchResult = runCommand('fetchmail -c 2>&1 || true', 15000);
  
  return `📧 **Email Check for ${CONFIG.email}**
- Folder: ${folderName}
- Filter: ${unreadFlag}
- Result: ${fetchResult.output || fetchResult.error || 'No new messages'}`;
}

/**
 * Create account on a website
 */
async function sonia_create_account({ website, username, email, password, full_name, details }) {
  if (!website) {
    return '❌ Website URL is required';
  }
  
  const accountEmail = email || CONFIG.email;
  const accountName = full_name || CONFIG.name;
  const accountUsername = username || 'sonia_' + Date.now();
  const accountPassword = password || 'Sonia' + Math.random().toString(36).slice(2) + '!';

  const task = `Go to ${website} and create a new account with Email: ${accountEmail}, Username: ${accountUsername}, Password: ${accountPassword}, Full Name: ${accountName}. Fill out the signup form and submit it.`;

  const result = runCommand(
    `openclaw agent --agent main -m "${task.replace(/"/g, '\\"')}" --timeout 180 2>&1`,
    200000
  );

  return `🔐 **Account Creation Attempted**
- Website: ${website}
- Email: ${accountEmail}
- Username: ${accountUsername}
- Password: ${accountPassword}
- Status: ${result.success ? 'Completed' : 'Failed'}
- Details: ${(result.output || result.error || '').substring(0, 500)}`;
}

/**
 * Post to social media
 */
async function sonia_social_post({ platform, content, hashtags }) {
  if (!platform || !content) {
    return '❌ Platform and content are required';
  }
  
  const hashtagStr = hashtags && Array.isArray(hashtags) ? hashtags.map(t => `#${t}`).join(' ') : '';
  const fullContent = `${content} ${hashtagStr}`.trim();

  const task = `Go to ${platform} and create a new post with the following content: "${fullContent}". Make sure to post successfully.`;

  const result = runCommand(
    `openclaw agent --agent main -m "${task.replace(/"/g, '\\"')}" --timeout 120 2>&1`,
    150000
  );

  return `📱 **Social Media Post**
- Platform: ${platform}
- Content: ${fullContent.substring(0, 100)}...
- Status: ${result.success ? 'Posted' : 'Failed'}
- Details: ${(result.output || result.error || '').substring(0, 300)}`;
}

/**
 * Engage with social media content
 */
async function sonia_social_engage({ platform, action, target_url, comment_text }) {
  if (!platform || !action || !target_url) {
    return '❌ Platform, action, and target_url are required';
  }
  
  const task = `Go to ${target_url} on ${platform} and perform the action: ${action}${action === 'comment' ? `. Write the comment: "${comment_text}"` : ''}. Confirm the action was completed.`;

  const result = runCommand(
    `openclaw agent --agent main -m "${task.replace(/"/g, '\\"')}" --timeout 90 2>&1`,
    120000
  );

  return `👍 **Social Engagement**
- Platform: ${platform}
- Action: ${action}
- Target: ${target_url}
- Status: ${result.success ? 'Completed' : 'Failed'}`;
}

/**
 * Browse web and perform actions
 */
async function sonia_browse_web({ url, extract_text }) {
  if (!url) {
    return '❌ URL is required';
  }
  
  let result = runCommand(`openclaw browser open "${url}" --browser-profile ${CONFIG.browser_profile} --timeout 30000 2>&1`);
  
  let extractedText = '';
  if (extract_text) {
    const snapshotResult = runCommand(`openclaw browser snapshot --browser-profile ${CONFIG.browser_profile} 2>&1`);
    extractedText = snapshotResult.output || snapshotResult.error || '';
  }

  return `🌐 **Web Browse**
- URL: ${url}
- Status: ${result.success ? 'Opened' : 'Failed'}
- Content: ${extractedText.substring(0, 500) || 'No content extracted'}`;
}

/**
 * Complete a complex task autonomously
 */
async function sonia_complete_task({ task, report_to, recipient }) {
  if (!task) {
    return '❌ Task description is required';
  }
  
  const reportMethod = report_to || 'whatsapp';
  const reportRecipient = recipient || CONFIG.whatsapp_default;

  const result = runCommand(
    `openclaw agent --agent main -m "${task.replace(/"/g, '\\"')}" --timeout 300 2>&1`,
    350000
  );

  const report = `Task Completed by Sonia\n\nTask: ${task}\n\nResult:\n${result.output || result.error || 'No output'}`;

  // Send report
  if (reportMethod === 'whatsapp' || reportMethod === 'both') {
    runCommand(`openclaw message send --target "${reportRecipient}" --message "${report.replace(/"/g, '\\"').substring(0, 2000)}" 2>&1`);
  }
  if (reportMethod === 'email' || reportMethod === 'both') {
    const emailRecip = reportRecipient.includes('@') ? reportRecipient : CONFIG.email;
    await sonia_send_email({
      to: emailRecip,
      subject: `Task Completed: ${task.substring(0, 50)}...`,
      body: report
    });
  }

  return `✅ **Task Completed**
- Task: ${task.substring(0, 100)}...
- Status: ${result.success ? 'Completed' : 'Attempted'}
- Report sent to: ${reportRecipient} (${reportMethod})`;
}

/**
 * Schedule a task for later
 */
async function sonia_schedule_task({ task, run_at, repeat }) {
  if (!task || !run_at) {
    return '❌ Task and run_at are required';
  }
  
  const jobId = `sonia_${Date.now()}`;
  const scriptPath = `${CONFIG.work_dir}/${jobId}.sh`;
  
  const script = `#!/bin/bash
# Sonia Scheduled Task: ${jobId}
export PATH=/usr/local/bin:/usr/bin:$PATH
openclaw agent --agent main -m "${task.replace(/"/g, '\\"')}" --timeout 300 2>&1 | tee ${CONFIG.work_dir}/${jobId}.log
openclaw message send --target "${CONFIG.whatsapp_default}" --message "Scheduled task completed: ${task.substring(0, 100)}" 2>&1
`;

  fs.writeFileSync(scriptPath, script);
  runCommand(`chmod +x ${scriptPath}`);

  let scheduleResult;
  if (repeat && repeat !== 'once') {
    const cronMap = {
      'daily': '0 9 * * *',
      'weekly': '0 9 * * 1',
      'monthly': '0 9 1 * *'
    };
    const cronExpr = cronMap[repeat] || '0 9 * * *';
    scheduleResult = runCommand(`(crontab -l 2>/dev/null; echo "${cronExpr} ${scriptPath}") | crontab -`);
  } else {
    scheduleResult = runCommand(`echo "${scriptPath}" | at ${run_at} 2>&1`);
  }

  return `⏰ **Task Scheduled**
- Job ID: ${jobId}
- Task: ${task.substring(0, 100)}...
- Run at: ${run_at}
- Repeat: ${repeat || 'once'}
- Status: ${scheduleResult.success ? 'Scheduled' : 'Failed'}`;
}

/**
 * Research a topic across multiple sources
 */
async function sonia_research({ topic, depth, output_format }) {
  if (!topic) {
    return '❌ Topic is required';
  }
  
  const researchDepth = depth || 'standard';
  const format = output_format || 'summary';

  const task = `Research the following topic: "${topic}". Search depth: ${researchDepth}. Compile findings into a ${format}. Include key facts and cite sources.`;

  const result = runCommand(
    `openclaw agent --agent main -m "${task.replace(/"/g, '\\"')}" --timeout 240 2>&1`,
    280000
  );

  return `🔍 **Research Complete**
- Topic: ${topic}
- Depth: ${researchDepth}
- Format: ${format}

**Findings:**
${(result.output || result.error || 'No findings').substring(0, 2000)}`;
}

// OpenClaw Extension Export
module.exports = function soniaExtension(ctx) {
  return {
    name: 'sonia',
    description: 'Sonia AI Assistant - Email, Social Media, Task Automation',
    
    tools: {
      sonia_send_email,
      sonia_check_email,
      sonia_create_account,
      sonia_social_post,
      sonia_social_engage,
      sonia_browse_web,
      sonia_complete_task,
      sonia_schedule_task,
      sonia_research
    }
  };
};
