# Telegram Bot Setup

Detailed setup of the Telegram interface for the travel agent.

## 1. Create the bot

1. In Telegram, message `@BotFather`:
   - `/newbot`
   - Choose a friendly name (shown to users): e.g., "My Travel Agent"
   - Choose a unique username ending in `bot`: e.g., `mytravelagent_personal_bot`
2. Save the API token (looks like `1234567890:ABCdef...`) — this is your `TELEGRAM_BOT_TOKEN`.
3. (Optional, recommended) Set bot description, about text, and profile picture via `@BotFather` for a polished UX.

## 2. Get your personal chat ID

1. Send any message to your new bot.
2. Open in browser:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. In the JSON response find: `"message": {..., "chat": {"id": <NUMBER>, ...}}`
4. That `<NUMBER>` (positive integer) is your `TELEGRAM_CHAT_ID`. Save it.

## 3. Install the Claude Code Telegram plugin

```bash
# add the official marketplace
claude plugin marketplace add anthropics/claude-plugins-official

# install telegram plugin
claude plugin install telegram@claude-plugins-official
```

## 4. Configure plugin secrets

The plugin reads `~/.claude/channels/telegram/.env`:

```bash
mkdir -p ~/.claude/channels/telegram
cat > ~/.claude/channels/telegram/.env <<EOF
TELEGRAM_BOT_TOKEN=<YOUR_BOT_TOKEN>
EOF
chmod 600 ~/.claude/channels/telegram/.env
```

## 5. Configure access control

Copy `access.json.example` from this repo:

```bash
cp telegram-bot/access.json.example ~/.claude/channels/telegram/access.json
```

Then edit `~/.claude/channels/telegram/access.json` and replace the placeholder with your chat ID:

```json
{
  "dmPolicy": "allowlist",
  "allowFrom": ["YOUR_TELEGRAM_CHAT_ID"],
  "groups": {},
  "pending": {}
}
```

Anyone NOT in `allowFrom` will be silently dropped — the bot won't respond to strangers.

## 6. Enable the plugin in your project

Edit `<project>/.claude/settings.json` (create the file if missing):

```json
{
  "enabledPlugins": {
    "telegram@claude-plugins-official": true
  }
}
```

Also add it to user-level `~/.claude/settings.json` for safety:

```json
{
  "enabledPlugins": {
    "telegram@claude-plugins-official": true
  }
}
```

## 7. Start the channels session

For an interactive session (testing):

```bash
claude --channels "plugin:telegram@claude-plugins-official" \
  --dangerously-skip-permissions \
  --debug-file /tmp/claude-channels-debug.log \
  --debug api,channels,mcp,plugin
```

> ⚠️ **Critical**: do NOT pass `--plugin-dir`. It loads the plugin as `inline` source, which mismatches the channel argument's expected source `claude-plugins-official`, and silently drops Telegram inbound notifications.

For an always-on background session, set up a LaunchAgent (macOS) / systemd unit (Linux):

### macOS LaunchAgent

The CLI `claude --channels` requires a TTY. Use a FIFO + `script` wrapper to provide one:

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/start-claude-channels.sh <<'EOF'
#!/bin/bash
export PATH="$HOME/.bun/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export HOME="$HOME"

FIFO="/tmp/claude-channels-stdin"
rm -f "$FIFO"
mkfifo "$FIFO"

exec tail -f "$FIFO" | script -q /dev/null \
  $HOME/.local/bin/claude \
  --channels "plugin:telegram@claude-plugins-official" \
  --dangerously-skip-permissions \
  --debug-file /tmp/claude-channels-debug.log \
  --debug api,channels,mcp,plugin
EOF
chmod +x ~/.local/bin/start-claude-channels.sh
```

LaunchAgent plist `~/Library/LaunchAgents/com.local.claude.travel-agent.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.local.claude.travel-agent</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/Users/YOU/.local/bin/start-claude-channels.sh</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/Users/YOU/.bun/bin:/Users/YOU/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>HOME</key>
    <string>/Users/YOU</string>
  </dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>WorkingDirectory</key><string>/Users/YOU/your-project-dir</string>
  <key>StandardOutPath</key><string>/Users/YOU/.local/share/claude-channels.log</string>
  <key>StandardErrorPath</key><string>/Users/YOU/.local/share/claude-channels-err.log</string>
</dict>
</plist>
```

Replace `/Users/YOU` with your actual home directory.

Load:
```bash
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.local.claude.travel-agent.plist
```

Verify:
```bash
launchctl list | grep claude.travel-agent
```

### Watchdog (recommended)

Bun (the Telegram polling MCP child) can crash silently while the parent claude session stays alive. A watchdog that runs every 10 minutes and verifies bun health:

```bash
cat > ~/.local/bin/claude-channels-watchdog.sh <<'EOF'
#!/bin/bash
LABEL="com.local.claude.travel-agent"
UID_NUM=$(id -u)

CLAUDE_PID=$(pgrep -fl "claude --channels plugin:telegram.*--debug-file" 2>/dev/null \
  | grep -v "^[0-9]* script " | awk '{print $1}' | head -1)
BUN_PID=$(pgrep -f "bun.*server.ts" | head -1)
BUN_TCP=$(lsof -p "$BUN_PID" 2>/dev/null | grep -c "149.154.166.*ESTABLISHED" || echo 0)

if [ -z "$CLAUDE_PID" ] || [ -z "$BUN_PID" ] || [ "$BUN_TCP" -lt 1 ]; then
  echo "[$(date)] Restart triggered: claude=$CLAUDE_PID bun=$BUN_PID tcp=$BUN_TCP" >> ~/.local/share/claude-channels-watchdog.log
  launchctl bootout "gui/${UID_NUM}/${LABEL}" 2>/dev/null || true
  sleep 2
  launchctl bootstrap "gui/${UID_NUM}" ~/Library/LaunchAgents/${LABEL}.plist
fi
EOF
chmod +x ~/.local/bin/claude-channels-watchdog.sh
```

Schedule via LaunchAgent `com.local.claude.travel-agent.watchdog.plist` with `StartInterval = 600` (every 10 min).

## 8. Test

Send a Telegram message to your bot (any text). The Claude Code session should:
1. Receive the inbound (visible in `/tmp/claude-channels-debug.log` as `notifications/claude/channel`)
2. Process the prompt
3. Reply via the plugin's `reply` tool

Verify with:
```bash
grep "Channel notifications registered" /tmp/claude-channels-debug.log  # should appear at startup
```

If you see `Channel notifications skipped: ...is from inline` instead, check that you're NOT passing `--plugin-dir`.

## 9. Voice messages (optional)

The plugin auto-saves voice attachments to `~/.claude/channels/telegram/inbox/<timestamp>-<id>.oga`. To transcribe in your prompts, integrate Whisper (CLI or API) — this is project-specific and not part of this travel agent's core.

Example — local Whisper:
```bash
~/.local/bin/whisper /path/to/voice.oga --model small --language Italian
```

For a turn-key voice setup, see the [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) ecosystem.
