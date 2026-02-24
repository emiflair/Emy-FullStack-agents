/**
 * Sonia AI Assistant Plugin for OpenClaw v3.0 - Money Making Edition
 * 
 * Autonomous AI assistant with capabilities for:
 * - Email (send/receive via Zoho)
 * - Browser automation (account creation, web interaction)
 * - Browser-based web search and trending research
 * - Social media posting and engagement (browser-based)
 * - Task persistence with SQLite database
 * - Follow-up reminders and proactive notifications
 * - Money Making: Freelance jobs, Micro-tasks, Trading, Affiliates
 * - Earnings tracking and financial reporting
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  email: 'sonia@wazhop.com',
  name: 'Sonia Wazhop',
  telegram_user: '6116923763',
  whatsapp_default: '+971551994544',
  browser_profile: 'server',
  work_dir: '/opt/emy-fullstack/sonia-workspace',
  db_path: '/opt/emy-fullstack/sonia-workspace/sonia_tasks.db',
  screenshots_dir: '/opt/emy-fullstack/sonia-workspace/screenshots'
};

// Ensure directories exist
try {
  [CONFIG.work_dir, CONFIG.screenshots_dir].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
} catch (e) {}

// Initialize SQLite database for task persistence
function initDatabase() {
  const initSQL = `
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      description TEXT,
      status TEXT DEFAULT 'pending',
      priority INTEGER DEFAULT 5,
      due_date TEXT,
      reminder_at TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
      completed_at TEXT,
      tags TEXT,
      notes TEXT
    );
    CREATE TABLE IF NOT EXISTS follow_ups (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      task_id INTEGER,
      contact TEXT,
      channel TEXT DEFAULT 'telegram',
      message TEXT,
      remind_at TEXT NOT NULL,
      sent INTEGER DEFAULT 0,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (task_id) REFERENCES tasks(id)
    );
    CREATE TABLE IF NOT EXISTS research_cache (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      query TEXT NOT NULL,
      results TEXT,
      source TEXT,
      cached_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS earnings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source TEXT NOT NULL,
      amount REAL NOT NULL,
      currency TEXT DEFAULT 'USD',
      description TEXT,
      job_id TEXT,
      platform TEXT,
      earned_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS jobs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      platform TEXT NOT NULL,
      job_id TEXT,
      title TEXT,
      description TEXT,
      budget TEXT,
      url TEXT,
      status TEXT DEFAULT 'found',
      applied_at TEXT,
      outcome TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS trades (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      exchange TEXT,
      pair TEXT,
      side TEXT,
      amount REAL,
      price REAL,
      profit_loss REAL,
      status TEXT DEFAULT 'open',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      closed_at TEXT
    );
  `;
  try {
    runCommand(`sqlite3 "${CONFIG.db_path}" "${initSQL.replace(/\n/g, ' ')}"`);
  } catch (e) {}
}
initDatabase();

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
 * Send notification via preferred channel (Telegram first, WhatsApp fallback)
 */
function sendNotification(message, channel = 'telegram') {
  if (channel === 'telegram') {
    const result = runCommand(`openclaw message send --channel telegram --target "${CONFIG.telegram_user}" --message "${message.replace(/"/g, '\\"')}" 2>&1`);
    if (result.success) return result;
  }
  // Fallback to WhatsApp
  return runCommand(`openclaw message send --channel whatsapp --message "${message.replace(/"/g, '\\"')}" 2>&1`);
}

// ============================================
// BROWSER-BASED WEB SEARCH
// ============================================

/**
 * Search the web using browser (Google, DuckDuckGo, or Brave)
 */
async function sonia_web_search({ query, engine, num_results, screenshot }) {
  if (!query) {
    return '❌ Search query is required';
  }

  const searchEngine = engine || 'google';
  const limit = num_results || 10;
  
  const searchUrls = {
    google: `https://www.google.com/search?q=${encodeURIComponent(query)}&num=${limit}`,
    duckduckgo: `https://duckduckgo.com/?q=${encodeURIComponent(query)}`,
    brave: `https://search.brave.com/search?q=${encodeURIComponent(query)}`
  };

  const url = searchUrls[searchEngine] || searchUrls.google;
  
  // Navigate to search page
  let result = runCommand(
    `openclaw browser navigate "${url}" --profile ${CONFIG.browser_profile} --wait 3000 2>&1`,
    60000
  );
  
  // Take screenshot if requested
  let screenshotPath = '';
  if (screenshot) {
    screenshotPath = `${CONFIG.screenshots_dir}/search_${Date.now()}.png`;
    runCommand(`openclaw browser screenshot --profile ${CONFIG.browser_profile} --output "${screenshotPath}" 2>&1`);
  }
  
  // Extract page content
  const snapshotResult = runCommand(
    `openclaw browser snapshot --profile ${CONFIG.browser_profile} --format text 2>&1`,
    30000
  );
  
  // Cache the results
  const cacheSQL = `INSERT INTO research_cache (query, results, source) VALUES ('${query.replace(/'/g, "''")}', '${(snapshotResult.output || '').substring(0, 5000).replace(/'/g, "''")}', '${searchEngine}')`;
  runCommand(`sqlite3 "${CONFIG.db_path}" "${cacheSQL}"`);

  return `🔍 **Web Search Results**
- Query: ${query}
- Engine: ${searchEngine}
- Status: ${result.success ? 'Completed' : 'Failed'}
${screenshot ? `- Screenshot: ${screenshotPath}` : ''}

**Results:**
${(snapshotResult.output || 'No results extracted').substring(0, 3000)}`;
}

/**
 * Get trending topics from various sources via browser
 */
async function sonia_get_trending({ source, category, country }) {
  const trendSource = source || 'twitter';
  const region = country || 'worldwide';
  
  const trendUrls = {
    twitter: 'https://twitter.com/explore/tabs/trending',
    reddit: 'https://www.reddit.com/r/popular/',
    google_trends: `https://trends.google.com/trends/trendingsearches/daily?geo=${region === 'worldwide' ? '' : region.toUpperCase()}`,
    hackernews: 'https://news.ycombinator.com/',
    producthunt: 'https://www.producthunt.com/'
  };

  const url = trendUrls[trendSource] || trendUrls.twitter;
  
  // Navigate to trending page
  let result = runCommand(
    `openclaw browser navigate "${url}" --profile ${CONFIG.browser_profile} --wait 5000 2>&1`,
    90000
  );
  
  // Take screenshot
  const screenshotPath = `${CONFIG.screenshots_dir}/trending_${trendSource}_${Date.now()}.png`;
  runCommand(`openclaw browser screenshot --profile ${CONFIG.browser_profile} --output "${screenshotPath}" 2>&1`);
  
  // Extract content
  const snapshotResult = runCommand(
    `openclaw browser snapshot --profile ${CONFIG.browser_profile} --format text 2>&1`,
    30000
  );

  return `📈 **Trending Topics**
- Source: ${trendSource}
- Category: ${category || 'general'}
- Region: ${region}
- Screenshot: ${screenshotPath}

**Trends:**
${(snapshotResult.output || 'Could not extract trends').substring(0, 3000)}`;
}

/**
 * Deep research on a topic using multiple browser searches
 */
async function sonia_deep_research({ topic, sources, save_report }) {
  if (!topic) {
    return '❌ Research topic is required';
  }

  const searchSources = sources || ['google', 'reddit', 'hackernews'];
  let fullReport = `# Research Report: ${topic}\n\nGenerated by Sonia on ${new Date().toISOString()}\n\n`;
  
  for (const source of searchSources) {
    let url;
    if (source === 'google') {
      url = `https://www.google.com/search?q=${encodeURIComponent(topic)}&num=20`;
    } else if (source === 'reddit') {
      url = `https://www.reddit.com/search/?q=${encodeURIComponent(topic)}&sort=relevance`;
    } else if (source === 'hackernews') {
      url = `https://hn.algolia.com/?q=${encodeURIComponent(topic)}`;
    } else if (source === 'youtube') {
      url = `https://www.youtube.com/results?search_query=${encodeURIComponent(topic)}`;
    } else {
      url = `https://www.google.com/search?q=${encodeURIComponent(topic + ' ' + source)}`;
    }

    runCommand(`openclaw browser navigate "${url}" --profile ${CONFIG.browser_profile} --wait 4000 2>&1`, 60000);
    const snapshot = runCommand(`openclaw browser snapshot --profile ${CONFIG.browser_profile} --format text 2>&1`, 30000);
    
    fullReport += `\n## ${source.toUpperCase()}\n\n${(snapshot.output || 'No data').substring(0, 2000)}\n`;
  }

  // Save report if requested
  let reportPath = '';
  if (save_report) {
    reportPath = `${CONFIG.work_dir}/research_${topic.replace(/[^a-z0-9]/gi, '_').substring(0, 30)}_${Date.now()}.md`;
    fs.writeFileSync(reportPath, fullReport);
  }

  return `🔬 **Deep Research Complete**
- Topic: ${topic}
- Sources searched: ${searchSources.join(', ')}
${reportPath ? `- Report saved: ${reportPath}` : ''}

${fullReport.substring(0, 4000)}`;
}

// ============================================
// BROWSER-BASED SOCIAL MEDIA
// ============================================

/**
 * Post to social media using browser automation
 */
async function sonia_social_post_browser({ platform, content, media_path, hashtags }) {
  if (!platform || !content) {
    return '❌ Platform and content are required';
  }
  
  const hashtagStr = hashtags && Array.isArray(hashtags) ? ' ' + hashtags.map(t => `#${t}`).join(' ') : '';
  const fullContent = `${content}${hashtagStr}`;

  const platformUrls = {
    twitter: 'https://twitter.com/compose/tweet',
    linkedin: 'https://www.linkedin.com/feed/',
    facebook: 'https://www.facebook.com/',
    instagram: 'https://www.instagram.com/',
    reddit: 'https://www.reddit.com/submit'
  };

  const url = platformUrls[platform.toLowerCase()] || platform;
  
  // Navigate to platform
  runCommand(`openclaw browser navigate "${url}" --profile ${CONFIG.browser_profile} --wait 5000 2>&1`, 60000);
  
  // Use agent to complete the posting task
  const task = `On the current page (${platform}), compose and publish a new post with this exact content: "${fullContent}". ${media_path ? `Also upload this image: ${media_path}` : ''} Make sure to click the post/submit button.`;
  
  const result = runCommand(
    `openclaw agent --agent main -m "${task.replace(/"/g, '\\"')}" --timeout 120 2>&1`,
    150000
  );

  // Screenshot for confirmation
  const screenshotPath = `${CONFIG.screenshots_dir}/post_${platform}_${Date.now()}.png`;
  runCommand(`openclaw browser screenshot --profile ${CONFIG.browser_profile} --output "${screenshotPath}" 2>&1`);

  return `📱 **Social Media Post**
- Platform: ${platform}
- Content: ${fullContent.substring(0, 100)}...
- Screenshot: ${screenshotPath}
- Status: ${result.success ? 'Posted' : 'Attempted'}
- Details: ${(result.output || result.error || '').substring(0, 500)}`;
}

/**
 * Monitor social media for mentions/topics using browser
 */
async function sonia_social_monitor({ platform, search_term, action_on_find }) {
  if (!platform || !search_term) {
    return '❌ Platform and search_term are required';
  }

  const searchUrls = {
    twitter: `https://twitter.com/search?q=${encodeURIComponent(search_term)}&f=live`,
    linkedin: `https://www.linkedin.com/search/results/content/?keywords=${encodeURIComponent(search_term)}`,
    reddit: `https://www.reddit.com/search/?q=${encodeURIComponent(search_term)}&sort=new`
  };

  const url = searchUrls[platform.toLowerCase()] || `${platform}/search?q=${encodeURIComponent(search_term)}`;
  
  runCommand(`openclaw browser navigate "${url}" --profile ${CONFIG.browser_profile} --wait 5000 2>&1`, 60000);
  
  const snapshot = runCommand(`openclaw browser snapshot --profile ${CONFIG.browser_profile} --format text 2>&1`, 30000);
  
  const screenshotPath = `${CONFIG.screenshots_dir}/monitor_${platform}_${Date.now()}.png`;
  runCommand(`openclaw browser screenshot --profile ${CONFIG.browser_profile} --output "${screenshotPath}" 2>&1`);

  return `👁️ **Social Media Monitor**
- Platform: ${platform}
- Search: ${search_term}
- Screenshot: ${screenshotPath}

**Found:**
${(snapshot.output || 'No results').substring(0, 3000)}`;
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

// ============================================
// TASK PERSISTENCE SYSTEM
// ============================================

/**
 * Create a new task with persistence
 */
async function sonia_create_task({ title, description, priority, due_date, tags, reminder }) {
  if (!title) {
    return '❌ Task title is required';
  }

  const taskPriority = priority || 5;
  const taskTags = tags ? (Array.isArray(tags) ? tags.join(',') : tags) : '';
  
  const insertSQL = `INSERT INTO tasks (title, description, priority, due_date, tags) VALUES ('${title.replace(/'/g, "''")}', '${(description || '').replace(/'/g, "''")}', ${taskPriority}, '${due_date || ''}', '${taskTags}')`;
  
  runCommand(`sqlite3 "${CONFIG.db_path}" "${insertSQL}"`);
  
  // Get the task ID
  const idResult = runCommand(`sqlite3 "${CONFIG.db_path}" "SELECT last_insert_rowid()"`);
  const taskId = idResult.output?.trim() || '0';

  // Set up reminder if requested
  if (reminder) {
    await sonia_set_follow_up({
      task_id: parseInt(taskId),
      remind_at: reminder,
      message: `Reminder: ${title}`
    });
  }

  return `✅ **Task Created**
- ID: ${taskId}
- Title: ${title}
- Priority: ${taskPriority}/10
- Due: ${due_date || 'No deadline'}
- Tags: ${taskTags || 'None'}
${reminder ? `- Reminder: ${reminder}` : ''}`;
}

/**
 * List tasks with filtering
 */
async function sonia_list_tasks({ status, priority_min, tag, limit }) {
  let whereClause = '1=1';
  if (status) whereClause += ` AND status='${status}'`;
  if (priority_min) whereClause += ` AND priority >= ${priority_min}`;
  if (tag) whereClause += ` AND tags LIKE '%${tag}%'`;
  
  const queryLimit = limit || 20;
  const sql = `SELECT id, title, status, priority, due_date, created_at FROM tasks WHERE ${whereClause} ORDER BY priority DESC, due_date ASC LIMIT ${queryLimit}`;
  
  const result = runCommand(`sqlite3 -header -column "${CONFIG.db_path}" "${sql}"`);

  return `📋 **Tasks**
${result.output || 'No tasks found'}`;
}

/**
 * Update task status
 */
async function sonia_update_task({ task_id, status, notes, priority }) {
  if (!task_id) {
    return '❌ Task ID is required';
  }

  let updates = [];
  if (status) updates.push(`status='${status}'`);
  if (notes) updates.push(`notes='${notes.replace(/'/g, "''")}'`);
  if (priority) updates.push(`priority=${priority}`);
  updates.push("updated_at=datetime('now')");
  
  if (status === 'completed') {
    updates.push("completed_at=datetime('now')");
  }

  const sql = `UPDATE tasks SET ${updates.join(', ')} WHERE id=${task_id}`;
  runCommand(`sqlite3 "${CONFIG.db_path}" "${sql}"`);

  return `✅ **Task Updated**
- ID: ${task_id}
- Status: ${status || 'unchanged'}`;
}

/**
 * Delete a task
 */
async function sonia_delete_task({ task_id }) {
  if (!task_id) {
    return '❌ Task ID is required';
  }

  runCommand(`sqlite3 "${CONFIG.db_path}" "DELETE FROM tasks WHERE id=${task_id}"`);
  runCommand(`sqlite3 "${CONFIG.db_path}" "DELETE FROM follow_ups WHERE task_id=${task_id}"`);

  return `🗑️ Task ${task_id} deleted`;
}

// ============================================
// FOLLOW-UP & REMINDER SYSTEM
// ============================================

/**
 * Set a follow-up reminder
 */
async function sonia_set_follow_up({ task_id, contact, channel, message, remind_at }) {
  if (!remind_at || !message) {
    return '❌ remind_at and message are required';
  }

  const followChannel = channel || 'telegram';
  const followContact = contact || CONFIG.telegram_user;
  
  const sql = `INSERT INTO follow_ups (task_id, contact, channel, message, remind_at) VALUES (${task_id || 'NULL'}, '${followContact}', '${followChannel}', '${message.replace(/'/g, "''")}', '${remind_at}')`;
  
  runCommand(`sqlite3 "${CONFIG.db_path}" "${sql}"`);
  
  const idResult = runCommand(`sqlite3 "${CONFIG.db_path}" "SELECT last_insert_rowid()"`);
  const followUpId = idResult.output?.trim() || '0';

  // Also add to system cron for execution
  const cronTime = remind_at; // Expected format: "HH:MM" or "YYYY-MM-DD HH:MM"
  const cronJob = `openclaw message send --channel ${followChannel} --target "${followContact}" --message "${message.replace(/"/g, '\\"')}" && sqlite3 "${CONFIG.db_path}" "UPDATE follow_ups SET sent=1 WHERE id=${followUpId}"`;
  
  // For simple time format, use at command
  runCommand(`echo '${cronJob}' | at ${remind_at} 2>/dev/null || true`);

  return `⏰ **Follow-up Set**
- ID: ${followUpId}
- Message: ${message.substring(0, 100)}...
- Remind at: ${remind_at}
- Channel: ${followChannel}
- Contact: ${followContact}`;
}

/**
 * List pending follow-ups
 */
async function sonia_list_follow_ups({ include_sent }) {
  const whereClause = include_sent ? '1=1' : 'sent=0';
  const sql = `SELECT id, message, remind_at, channel, sent FROM follow_ups WHERE ${whereClause} ORDER BY remind_at ASC LIMIT 50`;
  
  const result = runCommand(`sqlite3 -header -column "${CONFIG.db_path}" "${sql}"`);

  return `⏰ **Follow-ups**
${result.output || 'No follow-ups scheduled'}`;
}

/**
 * Process due follow-ups (called by cron)
 */
async function sonia_process_follow_ups() {
  const sql = `SELECT id, contact, channel, message FROM follow_ups WHERE sent=0 AND remind_at <= datetime('now')`;
  const result = runCommand(`sqlite3 -separator '|' "${CONFIG.db_path}" "${sql}"`);
  
  if (!result.output) {
    return '✅ No due follow-ups';
  }

  const lines = result.output.split('\n').filter(Boolean);
  let processed = 0;
  
  for (const line of lines) {
    const [id, contact, channel, message] = line.split('|');
    sendNotification(message, channel);
    runCommand(`sqlite3 "${CONFIG.db_path}" "UPDATE follow_ups SET sent=1 WHERE id=${id}"`);
    processed++;
  }

  return `✅ Processed ${processed} follow-ups`;
}

/**
 * Quick reminder - shortcut for simple reminders
 */
async function sonia_remind_me({ message, in_minutes, at_time }) {
  if (!message) {
    return '❌ Message is required';
  }

  let remindAt;
  if (in_minutes) {
    const futureDate = new Date(Date.now() + in_minutes * 60000);
    remindAt = futureDate.toISOString().slice(0, 16).replace('T', ' ');
  } else if (at_time) {
    remindAt = at_time;
  } else {
    return '❌ Either in_minutes or at_time is required';
  }

  return await sonia_set_follow_up({
    message: `🔔 Reminder: ${message}`,
    remind_at: remindAt,
    channel: 'telegram'
  });
}

/**
 * Daily summary of tasks and follow-ups
 */
async function sonia_daily_summary() {
  const pendingTasks = runCommand(`sqlite3 "${CONFIG.db_path}" "SELECT COUNT(*) FROM tasks WHERE status='pending'"`);
  const dueTodayTasks = runCommand(`sqlite3 "${CONFIG.db_path}" "SELECT COUNT(*) FROM tasks WHERE status='pending' AND date(due_date)=date('now')"`);
  const pendingFollowUps = runCommand(`sqlite3 "${CONFIG.db_path}" "SELECT COUNT(*) FROM follow_ups WHERE sent=0"`);
  const completedToday = runCommand(`sqlite3 "${CONFIG.db_path}" "SELECT COUNT(*) FROM tasks WHERE date(completed_at)=date('now')"`);

  const summary = `📊 **Daily Summary**

📋 Tasks:
- Pending: ${pendingTasks.output?.trim() || 0}
- Due Today: ${dueTodayTasks.output?.trim() || 0}
- Completed Today: ${completedToday.output?.trim() || 0}

⏰ Follow-ups Pending: ${pendingFollowUps.output?.trim() || 0}

Need anything else?`;

  sendNotification(summary, 'telegram');
  return summary;
}

/**
 * Send SMS via Twilio
 */
async function sonia_send_sms({ to, message }) {
  if (!to || !message) {
    return { success: false, error: 'Both "to" phone number and "message" are required' };
  }

  // Ensure phone number has + prefix
  const phoneNumber = to.startsWith('+') ? to : `+${to}`;
  
  // Use the sonia-sms script
  const result = runCommand(`/usr/local/bin/sonia-sms "${phoneNumber}" "${message.replace(/"/g, '\\"')}"`, 30000);
  
  if (result.success && result.output) {
    try {
      const response = JSON.parse(result.output);
      if (response.sid) {
        return {
          success: true,
          message_sid: response.sid,
          to: response.to,
          status: response.status,
          message: `SMS sent to ${phoneNumber}`
        };
      } else if (response.code) {
        return { success: false, error: response.message || 'Twilio error', code: response.code };
      }
    } catch (e) {
      return { success: true, output: result.output };
    }
  }
  
  return { success: false, error: result.error || 'Failed to send SMS' };
}

/**
 * Receive/check SMS messages
 */
async function sonia_check_sms({ limit = 10 }) {
  const twilioSid = process.env.TWILIO_ACCOUNT_SID || '';
  const twilioToken = process.env.TWILIO_AUTH_TOKEN || '';
  
  if (!twilioSid || !twilioToken) {
    return { success: false, error: 'Twilio credentials not configured' };
  }
  
  const result = runCommand(`curl -s "https://api.twilio.com/2010-04-01/Accounts/${twilioSid}/Messages.json?PageSize=${limit}" -u "${twilioSid}:${twilioToken}"`, 30000);
  
  if (result.success && result.output) {
    try {
      const data = JSON.parse(result.output);
      const messages = (data.messages || []).map(m => ({
        from: m.from,
        to: m.to,
        body: m.body,
        status: m.status,
        date: m.date_sent,
        direction: m.direction
      }));
      return { success: true, messages, count: messages.length };
    } catch (e) {
      return { success: false, error: 'Failed to parse SMS response' };
    }
  }
  
  return { success: false, error: result.error || 'Failed to fetch SMS' };
}

// ============================================
// MONEY-MAKING MODULE - Autonomous Income
// ============================================

/**
 * Search for freelance jobs on various platforms
 */
async function sonia_find_jobs({ platform = 'all', skills = [], min_budget = 0, keywords = '' }) {
  const platforms = {
    upwork: 'https://www.upwork.com/nx/search/jobs/?q=',
    fiverr: 'https://www.fiverr.com/search/gigs?query=',
    freelancer: 'https://www.freelancer.com/jobs/?keyword=',
    peopleperhour: 'https://www.peopleperhour.com/freelance-jobs?q=',
    guru: 'https://www.guru.com/d/jobs/q/',
    toptal: 'https://www.toptal.com/freelance-jobs'
  };
  
  const searchTerms = keywords || skills.join(' ') || 'ai automation python javascript';
  const jobs = [];
  
  const platformsToSearch = platform === 'all' 
    ? Object.keys(platforms) 
    : [platform];
  
  for (const plat of platformsToSearch.slice(0, 3)) {
    if (!platforms[plat]) continue;
    
    const url = platforms[plat] + encodeURIComponent(searchTerms);
    const result = runCommand(`chromium --headless --dump-dom "${url}" 2>/dev/null | head -500`, 60000);
    
    if (result.success) {
      // Parse job listings (simplified - real implementation would parse HTML properly)
      const jobMatches = result.output.match(/(?:job|gig|project)[^<]{20,200}/gi) || [];
      jobMatches.slice(0, 5).forEach((match, i) => {
        jobs.push({
          platform: plat,
          title: match.slice(0, 100),
          url: url,
          found_at: new Date().toISOString()
        });
      });
    }
  }
  
  // Save jobs to database
  for (const job of jobs) {
    runCommand(`sqlite3 "${CONFIG.db_path}" "INSERT INTO jobs (platform, title, url, status) VALUES ('${job.platform}', '${job.title.replace(/'/g, "''")}', '${job.url}', 'found')"`);
  }
  
  sendNotification(`🔍 Found ${jobs.length} potential jobs across ${platformsToSearch.length} platforms`, 'telegram');
  
  return { success: true, jobs, count: jobs.length };
}

/**
 * Apply to a job (browser-based)
 */
async function sonia_apply_job({ platform, job_url, cover_letter, bid_amount }) {
  if (!job_url) {
    return { success: false, error: 'Job URL required' };
  }
  
  // Navigate to job and take screenshot for review
  const screenshot = `${CONFIG.screenshots_dir}/job_${Date.now()}.png`;
  runCommand(`chromium --headless --screenshot="${screenshot}" "${job_url}" 2>/dev/null`);
  
  // Log the application attempt
  runCommand(`sqlite3 "${CONFIG.db_path}" "INSERT INTO jobs (platform, url, status, applied_at) VALUES ('${platform || 'unknown'}', '${job_url}', 'applied', datetime('now'))"`);
  
  sendNotification(`📝 Job application prepared for review:\n${job_url}\nBid: $${bid_amount || 'TBD'}\n\nScreenshot saved. Awaiting confirmation to submit.`, 'telegram');
  
  return { 
    success: true, 
    status: 'prepared',
    screenshot,
    message: 'Application prepared - needs your confirmation to submit'
  };
}

/**
 * Search for micro-tasks and quick gigs
 */
async function sonia_find_micro_tasks({ category = 'all' }) {
  const platforms = [
    { name: 'Amazon MTurk', url: 'https://worker.mturk.com/', type: 'microtask' },
    { name: 'Clickworker', url: 'https://www.clickworker.com/clickworker/', type: 'microtask' },
    { name: 'Appen', url: 'https://connect.appen.com/', type: 'ai-training' },
    { name: 'Remotasks', url: 'https://www.remotasks.com/', type: 'ai-training' },
    { name: 'Swagbucks', url: 'https://www.swagbucks.com/', type: 'surveys' },
    { name: 'UserTesting', url: 'https://www.usertesting.com/', type: 'testing' },
    { name: 'Testlio', url: 'https://testlio.com/', type: 'testing' }
  ];
  
  const tasks = [];
  
  for (const platform of platforms.slice(0, 3)) {
    const result = runCommand(`curl -s -A "Mozilla/5.0" "${platform.url}" | head -200`, 30000);
    if (result.success) {
      tasks.push({
        platform: platform.name,
        url: platform.url,
        type: platform.type,
        status: 'available'
      });
    }
  }
  
  return { 
    success: true, 
    platforms: tasks,
    message: 'Micro-task platforms checked. Sign up and connect accounts for automated task completion.'
  };
}

/**
 * Get crypto prices and market data
 */
async function sonia_get_crypto_prices({ coins = ['bitcoin', 'ethereum'] }) {
  const coinList = coins.join(',');
  const result = runCommand(`curl -s "https://api.coingecko.com/api/v3/simple/price?ids=${coinList}&vs_currencies=usd&include_24hr_change=true"`, 15000);
  
  if (result.success && result.output) {
    try {
      const prices = JSON.parse(result.output);
      return { success: true, prices };
    } catch (e) {
      return { success: false, error: 'Failed to parse prices' };
    }
  }
  
  return { success: false, error: result.error };
}

/**
 * Execute crypto trade (requires exchange API keys)
 */
async function sonia_crypto_trade({ exchange = 'binance', action, pair, amount, price_type = 'market' }) {
  // Check for API keys
  const apiKey = process.env[`${exchange.toUpperCase()}_API_KEY`];
  const apiSecret = process.env[`${exchange.toUpperCase()}_API_SECRET`];
  
  if (!apiKey || !apiSecret) {
    return { 
      success: false, 
      error: `${exchange} API keys not configured. Set ${exchange.toUpperCase()}_API_KEY and ${exchange.toUpperCase()}_API_SECRET`,
      setup_instructions: `1. Create API key on ${exchange}\n2. Add to server .env\n3. Restart Sonia`
    };
  }
  
  // For safety, require confirmation for real trades
  const tradeId = Date.now();
  runCommand(`sqlite3 "${CONFIG.db_path}" "INSERT INTO trades (exchange, pair, side, amount, status) VALUES ('${exchange}', '${pair}', '${action}', ${amount}, 'pending_confirmation')"`);
  
  sendNotification(`⚠️ Trade confirmation needed:\n${action.toUpperCase()} ${amount} ${pair} on ${exchange}\n\nReply "CONFIRM TRADE ${tradeId}" to execute`, 'telegram');
  
  return {
    success: true,
    status: 'pending_confirmation',
    trade_id: tradeId,
    message: 'Trade requires your confirmation via Telegram'
  };
}

/**
 * Monitor trading signals and opportunities
 */
async function sonia_trading_signals({ pairs = ['BTCUSDT', 'ETHUSDT'] }) {
  const signals = [];
  
  // Get Fear & Greed Index
  const fgiResult = runCommand(`curl -s "https://api.alternative.me/fng/?limit=1"`, 10000);
  let fearGreed = null;
  if (fgiResult.success) {
    try {
      const fgi = JSON.parse(fgiResult.output);
      fearGreed = fgi.data?.[0];
    } catch (e) {}
  }
  
  // Get trending coins
  const trendingResult = runCommand(`curl -s "https://api.coingecko.com/api/v3/search/trending"`, 15000);
  let trending = [];
  if (trendingResult.success) {
    try {
      const data = JSON.parse(trendingResult.output);
      trending = data.coins?.slice(0, 5).map(c => c.item?.name) || [];
    } catch (e) {}
  }
  
  return {
    success: true,
    fear_greed_index: fearGreed ? { value: fearGreed.value, classification: fearGreed.value_classification } : null,
    trending_coins: trending,
    recommendation: fearGreed?.value < 25 ? 'EXTREME FEAR - Potential buying opportunity' : 
                    fearGreed?.value > 75 ? 'EXTREME GREED - Consider taking profits' : 
                    'NEUTRAL - Monitor market'
  };
}

/**
 * Track earnings and income
 */
async function sonia_record_earning({ source, amount, currency = 'USD', description = '', platform = '' }) {
  if (!source || !amount) {
    return { success: false, error: 'Source and amount required' };
  }
  
  runCommand(`sqlite3 "${CONFIG.db_path}" "INSERT INTO earnings (source, amount, currency, description, platform) VALUES ('${source}', ${amount}, '${currency}', '${description.replace(/'/g, "''")}', '${platform}')"`);
  
  sendNotification(`💰 Earning recorded: $${amount} ${currency} from ${source}`, 'telegram');
  
  return { success: true, message: `Recorded $${amount} from ${source}` };
}

/**
 * Get earnings summary
 */
async function sonia_earnings_report({ period = 'all' }) {
  let dateFilter = '';
  if (period === 'today') dateFilter = "AND date(earned_at) = date('now')";
  else if (period === 'week') dateFilter = "AND earned_at >= datetime('now', '-7 days')";
  else if (period === 'month') dateFilter = "AND earned_at >= datetime('now', '-30 days')";
  
  const totalResult = runCommand(`sqlite3 "${CONFIG.db_path}" "SELECT COALESCE(SUM(amount), 0) FROM earnings WHERE 1=1 ${dateFilter}"`);
  const bySourceResult = runCommand(`sqlite3 "${CONFIG.db_path}" "SELECT source, SUM(amount) FROM earnings WHERE 1=1 ${dateFilter} GROUP BY source ORDER BY SUM(amount) DESC LIMIT 10"`);
  const countResult = runCommand(`sqlite3 "${CONFIG.db_path}" "SELECT COUNT(*) FROM earnings WHERE 1=1 ${dateFilter}"`);
  
  const total = parseFloat(totalResult.output) || 0;
  const sources = bySourceResult.output?.split('\n').filter(Boolean).map(line => {
    const [source, amount] = line.split('|');
    return { source, amount: parseFloat(amount) || 0 };
  }) || [];
  
  const report = `📊 **Earnings Report (${period})**\n\n💰 Total: $${total.toFixed(2)}\n📈 Transactions: ${countResult.output || 0}\n\n**By Source:**\n${sources.map(s => `• ${s.source}: $${s.amount.toFixed(2)}`).join('\n') || 'No earnings yet'}`;
  
  sendNotification(report, 'telegram');
  
  return { success: true, total, sources, period, transactions: parseInt(countResult.output) || 0 };
}

/**
 * Find affiliate programs and opportunities
 */
async function sonia_find_affiliates({ niche = 'technology' }) {
  const affiliateNetworks = [
    { name: 'Amazon Associates', url: 'https://affiliate-program.amazon.com/', commission: '1-10%' },
    { name: 'ShareASale', url: 'https://www.shareasale.com/', commission: 'Varies' },
    { name: 'CJ Affiliate', url: 'https://www.cj.com/', commission: 'Varies' },
    { name: 'Rakuten', url: 'https://rakutenadvertising.com/', commission: 'Varies' },
    { name: 'ClickBank', url: 'https://www.clickbank.com/', commission: 'Up to 75%' },
    { name: 'Impact', url: 'https://impact.com/', commission: 'Varies' },
    { name: 'Awin', url: 'https://www.awin.com/', commission: 'Varies' }
  ];
  
  return {
    success: true,
    networks: affiliateNetworks,
    recommendation: `For ${niche} niche, consider: Amazon Associates for products, ShareASale for variety, or niche-specific programs.`,
    next_steps: [
      '1. Sign up for affiliate networks',
      '2. Get approved for relevant programs',
      '3. Share affiliate links via content/social media',
      '4. Track conversions and earnings'
    ]
  };
}

/**
 * Content monetization opportunities
 */
async function sonia_content_monetization({ platform = 'all' }) {
  const opportunities = [
    { platform: 'YouTube', requirements: '1000 subs, 4000 watch hours', earning: 'Ad revenue, sponsorships' },
    { platform: 'TikTok', requirements: '10k followers, 100k views', earning: 'Creator Fund, sponsorships' },
    { platform: 'Medium', requirements: 'Partner Program', earning: 'Per-read earnings' },
    { platform: 'Substack', requirements: 'None', earning: 'Paid subscriptions' },
    { platform: 'Gumroad', requirements: 'None', earning: 'Digital product sales' },
    { platform: 'Teachable', requirements: 'None', earning: 'Course sales' },
    { platform: 'Patreon', requirements: 'None', earning: 'Monthly subscriptions' }
  ];
  
  return {
    success: true,
    opportunities,
    ai_content_ideas: [
      'AI automation tutorials',
      'Coding guides and templates',
      'Tech reviews and comparisons',
      'Productivity tools and tips'
    ]
  };
}

/**
 * Auto-generate income opportunities report
 */
async function sonia_money_opportunities() {
  // Check current market conditions
  const cryptoResult = await sonia_get_crypto_prices({ coins: ['bitcoin', 'ethereum'] });
  const signalsResult = await sonia_trading_signals({});
  const earningsResult = await sonia_earnings_report({ period: 'month' });
  
  // Find new jobs
  const jobsResult = await sonia_find_jobs({ keywords: 'ai automation bot python', platform: 'upwork' });
  
  const report = `
🤖 **Sonia Money Opportunities Report**

📈 **Market Conditions:**
${signalsResult.fear_greed_index ? `Fear & Greed: ${signalsResult.fear_greed_index.value} (${signalsResult.fear_greed_index.classification})` : 'Unable to fetch'}
${signalsResult.recommendation || ''}

💼 **Jobs Found:** ${jobsResult.count || 0} new opportunities

💰 **This Month's Earnings:** $${earningsResult.total?.toFixed(2) || '0.00'}

🎯 **Recommended Actions:**
1. ${signalsResult.fear_greed_index?.value < 30 ? 'Consider crypto positions - market fearful' : 'Monitor crypto markets'}
2. Apply to ${jobsResult.count || 0} matching freelance jobs
3. Check micro-task platforms for quick earnings
4. Create content for passive income

Need me to execute any of these?
`;
  
  sendNotification(report, 'telegram');
  
  return { 
    success: true, 
    report,
    market: signalsResult,
    jobs: jobsResult.count,
    monthly_earnings: earningsResult.total
  };
}

// OpenClaw Extension Export
module.exports = function soniaExtension(ctx) {
  return {
    name: 'sonia',
    description: 'Sonia AI Assistant v3.0 - Money Making Edition: Jobs, Trading, Micro-tasks, Earnings Tracking',
    
    tools: {
      // Email
      sonia_send_email,
      sonia_check_email,
      
      // Browser-based Web Search
      sonia_web_search,
      sonia_get_trending,
      sonia_deep_research,
      
      // Browser-based Social Media
      sonia_social_post_browser,
      sonia_social_monitor,
      
      // Legacy (still available)
      sonia_create_account,
      sonia_social_post,
      sonia_social_engage,
      sonia_browse_web,
      sonia_complete_task,
      sonia_schedule_task,
      sonia_research,
      
      // Task Persistence
      sonia_create_task,
      sonia_list_tasks,
      sonia_update_task,
      sonia_delete_task,
      
      // Follow-ups & Reminders
      sonia_set_follow_up,
      sonia_list_follow_ups,
      sonia_process_follow_ups,
      sonia_remind_me,
      sonia_daily_summary,
      
      // SMS via Twilio
      sonia_send_sms,
      sonia_check_sms,
      
      // Money Making - Freelance & Jobs
      sonia_find_jobs,
      sonia_apply_job,
      sonia_find_micro_tasks,
      
      // Money Making - Trading
      sonia_get_crypto_prices,
      sonia_crypto_trade,
      sonia_trading_signals,
      
      // Money Making - Earnings & Tracking
      sonia_record_earning,
      sonia_earnings_report,
      
      // Money Making - Passive Income
      sonia_find_affiliates,
      sonia_content_monetization,
      sonia_money_opportunities
    }
  };
};
