---
name: channel-status
description: Check if the herokid notification channel is running and show stats.
user_invocable: true
---

# Channel Status Check

Run this command to check the channel:

```bash
curl -s http://127.0.0.1:9999/health 2>/dev/null || echo '{"status":"offline"}'
```

If the status is "ok", the channel is running. The response includes:
- `messages`: total messages pushed this session
- `last`: the type and time of the last message

If the status is "offline", the channel server is not running. Start Claude Code with:
```
claude --dangerously-load-development-channels server:herokid-channel
```
