# /monitor-stop Command

Stop the Pipeline Monitor background server.

## Usage

When the user types `/monitor-stop`:

1. Kill any process running on port 8111
2. Confirm what was stopped

## Implementation

Execute the following:

```bash
echo "Stopping Pipeline Monitor server..."

# Kill server (port 8111)
if lsof -ti :8111 > /dev/null 2>&1; then
  lsof -ti :8111 | xargs kill -9 2>/dev/null
  echo "Stopped Pipeline Monitor server"
else
  echo "Pipeline Monitor server was not running"
fi

echo ""
echo "Done. Use /monitor to start server again."
```

## Notes

- Safe to run even if server isn't running
- Uses `kill -9` to ensure process stops
- Does not affect other processes on different ports
