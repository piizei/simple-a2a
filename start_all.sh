#!/bin/bash
# filepath: c:\dev\a2a\start_all.sh

# Function to kill all background jobs on exit
cleanup() {
    echo -e "\n================================"
    echo "Stopping all agents..."
    # Kill all child processes
    pkill -P $$
    exit
}

# Set up trap to call cleanup function on script exit
trap cleanup EXIT INT TERM

echo "Starting Blog Writing System..."
echo "================================"

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start critic agent
echo "Starting Critic Agent on port 8001..."
(cd "$SCRIPT_DIR/critic" && uv run python __main__.py) &

# Start writer agent
echo "Starting Writer Agent on port 8002..."
(cd "$SCRIPT_DIR/writer" && uv run python __main__.py) &

# Give the remote agents a moment to start
sleep 2

# Start blog coordinator agent
echo "Starting Blog Coordinator Agent on port 8000..."
(cd "$SCRIPT_DIR" && uv run python blogging_agent.py) &

echo "================================"
echo "All agents started!"
echo "Access the web UI at: http://localhost:8000"
echo "Press Ctrl+C to stop all agents"
echo "================================"

# Wait forever (until interrupted)
while true; do
    sleep 1
done