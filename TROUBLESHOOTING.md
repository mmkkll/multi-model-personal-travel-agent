# Troubleshooting

Real-world issues encountered during development, with fixes that worked.

## Telegram inbound silence

**Symptom**: User sends a message to the bot. Telegram client shows the message as "delivered" (double check), but the agent never replies.

**Diagnostic**:
```bash
# 1. Check if the bot is receiving updates from Telegram
curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates"

# 2. If queue is non-empty, bun isn't consuming → restart
# 3. If queue is empty, bun consumed but Claude session didn't process → check Claude debug
```

**Most common cause**: `--plugin-dir` flag in your channels session command. This loads the plugin as `inline` source, which mismatches the `--channels plugin:telegram@claude-plugins-official` argument's expected source (the marketplace). Result: Claude silently drops MCP `notifications/claude/channel`.

**Fix**: remove `--plugin-dir` from your invocation. Let Claude resolve the plugin via `enabledPlugins` in `~/.claude/settings.json` and `<project>/.claude/settings.json`.

```bash
# WRONG (causes silent drop):
claude --channels "plugin:telegram@claude-plugins-official" --plugin-dir <path>

# RIGHT:
claude --channels "plugin:telegram@claude-plugins-official" --dangerously-skip-permissions
```

**Verify the fix**: enable debug logging in the wrapper:
```bash
claude --channels "plugin:telegram@claude-plugins-official" \
  --dangerously-skip-permissions \
  --debug-file /tmp/claude-channels-debug.log \
  --debug api,channels,mcp,plugin

# Then check:
grep "Channel notifications" /tmp/claude-channels-debug.log
```

You want to see:
```
[DEBUG] MCP server "plugin:telegram:telegram": Channel notifications registered
```

NOT:
```
[DEBUG] MCP server "plugin:telegram:telegram": Channel notifications skipped: ...is from inline
```

## Bun child dies silently

**Symptom**: Chain looks healthy at process level (claude --channels running), but messages stop being processed mid-day. Telegram queue accumulates.

**Diagnostic**:
```bash
pgrep -lf "bun.*server.ts"   # should return a PID
lsof -p <bun-pid> | grep TCP # should show 2 connections to 149.154.166.* (Telegram API)
```

If bun is missing or has 0 TCP connections, the MCP child died.

**Fix** — add a watchdog (LaunchAgent or systemd) that periodically checks bun + restarts the chain:

```bash
#!/bin/bash
# minimal watchdog
LABEL="com.local.travel-agent.channels"
UID_NUM=$(id -u)

CLAUDE_PID=$(pgrep -fl "claude --channels plugin:telegram.*--debug-file" 2>/dev/null \
  | grep -v "^[0-9]* script " | awk '{print $1}' | head -1)
BUN_PID=$(pgrep -f "bun.*server.ts" | head -1)
BUN_TCP=$(lsof -p "$BUN_PID" 2>/dev/null | grep -c "149.154.166.*ESTABLISHED" || echo 0)

if [ -z "$CLAUDE_PID" ] || [ -z "$BUN_PID" ] || [ "$BUN_TCP" -lt 1 ]; then
  echo "Restarting channels chain..."
  launchctl bootout "gui/${UID_NUM}/${LABEL}" 2>/dev/null || true
  sleep 2
  launchctl bootstrap "gui/${UID_NUM}" "$HOME/Library/LaunchAgents/${LABEL}.plist"
fi
```

Schedule via `StartInterval=600` (every 10 min) in a LaunchAgent plist.

## Mac sleeps and the bot goes offline

**Symptom**: After leaving the Mac unattended for hours, returning to find no messages were processed during that time. Telegram retention is 24h max, so messages older than that are unrecoverable.

**Cause**: Default Mac sleep settings (`pmset sleep 1` = sleep after 1 min idle when display sleeps) suspend bun + claude process, dropping the polling TCP connection.

**Fix**:
```bash
sudo pmset -a sleep 0 womp 1 powernap 1 tcpkeepalive 1
```

This disables system sleep entirely on AC power. For belt-and-suspenders, add a permanent caffeinate LaunchAgent:

```xml
<!-- ~/Library/LaunchAgents/com.local.caffeinate.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.local.caffeinate</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-d</string><string>-i</string><string>-m</string><string>-s</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>
```

## Duffel returns `insufficient_permissions`

**Symptom**:
```json
{
  "errors": [{
    "title": "Insufficient permissions",
    "message": "This endpoint requires a token with 'air.offer_requests.create' permission.",
    "code": "insufficient_permissions"
  }]
}
```

**Cause**: token was created as Read-only. `POST /air/offer_requests` is technically a write operation in Duffel's permission model (it creates a search resource on their side).

**Fix**: regenerate the token with **Read & Write** scope (or "Full Access" if your Duffel dashboard shows it that way). Even though we never call `/orders` or `/payments`, the search endpoint requires `create`.

## Gemini returns 503 UNAVAILABLE

**Symptom**:
```json
{"error": {"code": 503, "status": "UNAVAILABLE", "message": "...high demand..."}}
```

**Cause**: pinned to a specific model version (e.g., `gemini-2.5-flash`) that's temporarily overloaded.

**Fix**: use the auto-routing alias `gemini-flash-latest`:

```
# In n8n Gemini HTTP node URL:
https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={{ $env.GEMINI_API_KEY }}
```

`-latest` aliases auto-route to whichever variant is least loaded.

## Workflow returns all empty fields

**Symptom**: Webhook returns valid JSON but all 5 fields (`gemini`, `perplexity`, `openai`, `duffel`, `gmaps`) are empty or contain errors.

**Likely cause**: Extract Params node failed (no `OPENAI_API_KEY` in n8n env, or auth header malformed). Without parsed params, downstream nodes have nothing to work with.

**Fix**:
1. Check n8n Executions tab → click the failed execution → inspect `Extract Params` node output.
2. If you see `401 Unauthorized` from OpenAI, set `OPENAI_API_KEY` correctly.
3. If you see "JSON parse error", check the prompt — make sure it has `response_format: {type: "json_object"}` and instructs the model to return JSON only.

## n8n DB-edit doesn't persist

**Symptom**: edited workflow nodes via SQLite directly. Changes appear in `claude plugin list` or n8n UI initially, but revert after restart.

**Cause**: n8n uses TWO tables for workflows: `workflow_entity` (active) and `workflow_history` (versions). Editing only one is partial.

**Fix**: update both atomically:
```sql
UPDATE workflow_entity SET nodes = '...', connections = '...' WHERE id = '<workflow-id>';
UPDATE workflow_history SET nodes = '...', connections = '...' WHERE workflowId = '<workflow-id>';
```
Then restart n8n.

## Multi-origin Code node: `fetch is not defined`

**Symptom**: the Duffel multi-origin Code node throws `ReferenceError: fetch is not defined`.

**Cause**: n8n's Code node sandbox in 2.18.x doesn't expose Node 18's global `fetch`. You have to use n8n's HTTP helper.

**Fix**: in the Code node, replace `fetch(...)` with `this.helpers.httpRequest(...)`:

```javascript
const data = await this.helpers.httpRequest({
  method: 'POST',
  url: 'https://api.duffel.com/air/offer_requests',
  headers: { Authorization: `Bearer ${TOKEN}`, 'Duffel-Version': 'v2' },
  body: { /* ... */ },
  json: true,
  timeout: 30000
});
```

## Telegram client shows blue ✓✓ but bot doesn't respond

**Symptom**: your sent message has TWO blue checkmarks (= delivered AND read by bot), but no reply arrives.

**Interpretation**: bun successfully consumed the update from Telegram (which is what marks it "read" from Telegram's perspective). The bug is downstream — claude isn't processing the inbound notification. See "Telegram inbound silence" above for full diagnostics.

**Quick check**:
```bash
grep "Channel notifications" /tmp/claude-channels-debug.log | tail -5
```

If you see `skipped`, the plugin isn't registered. Remove `--plugin-dir` from your wrapper.

## Notion update fails with "no matches found"

**Symptom**: `notion-update-page` with `update_content` command returns `validation_error` saying the `old_str` doesn't match.

**Cause**: Notion's markdown serializer doesn't always round-trip exactly — formatting characters, escapes, or spacing can drift between fetch and update.

**Fix**: use `replace_content` instead of `update_content` when doing larger rewrites. It blanket-replaces the page body. Use `update_content` only for small surgical edits where you've JUST fetched the exact source string.

## Workflow takes >2 minutes (timeout)

**Symptom**: webhook curl request times out before getting a response.

**Cause**: one of the LLM nodes is slow or hanging. Default n8n webhook timeout is 120s.

**Fix**:
1. In each HTTP node, set `options.timeout` to 30000ms (30s).
2. Set `onError: continueRegularOutput` on every HTTP node so a single slow node doesn't block the Merge.
3. If you need a global timeout shorter than n8n's default, configure `EXECUTIONS_TIMEOUT_MAX` in n8n's environment.

## Logs are noisy / can't find the actual error

**General workflow** for any obscure issue:

1. Enable Claude Code debug: `--debug-file /tmp/claude-channels-debug.log --debug api,channels,mcp,plugin`
2. Capture bun stderr by editing the plugin's `package.json` `start` script:
   ```json
   "start": "bun install --no-summary && bun server.ts 2>>/tmp/bun-debug.log"
   ```
3. Watch n8n's Executions tab during a live test.
4. Add `console.log(JSON.stringify(...))` statements in the Code nodes — they show up in n8n's per-node output.
5. Search the JSON debug log with `jq 'select(.severity=="ERROR")'`.
