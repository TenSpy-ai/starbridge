# /monitor Command

Start the Pipeline Monitor server (if needed) and open the UI in your browser.

## Usage

When the user types `/monitor`:

1. Check if the server (port 8111) is running
2. If not running, start it in the background
3. Open the browser to http://localhost:8111

## Implementation

Execute the following:

```bash
PROJECT_DIR="/Users/oliviagao/project/starbridge"
LOG_FILE="/tmp/pipeline-monitor.log"

# Check and start server if needed
if ! lsof -i :8111 > /dev/null 2>&1; then
  echo "Starting Pipeline Monitor on port 8111..."
  cd "$PROJECT_DIR" && python -m agent.server > "$LOG_FILE" 2>&1 &
  sleep 2
fi

# Verify server started
if ! lsof -i :8111 > /dev/null 2>&1; then
  echo "ERROR: Server failed to start. Check $LOG_FILE for details."
  exit 1
fi

# Open browser
open http://localhost:8111
echo "Pipeline Monitor opened in browser"
echo ""
echo "Server running in background. Use /monitor-stop to stop."
echo "Log: $LOG_FILE"
```

## Notes

- Server runs in background — use `/monitor-stop` to stop it
- Logs are written to `/tmp/pipeline-monitor.log`
- Server persists until stopped or Mac restarts
- Serves pipeline-explorer.html with List, Monitor, and Diagram views
- Monitor view lets you launch pipeline runs and watch them execute in real-time
