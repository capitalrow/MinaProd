#!/bin/bash
# ============================================================
# Mina Performance Validation Runner
# Runs backend + socket load tests + k6 benchmarks sequentially
# ============================================================

# --- CONFIG ---
PORT=5000
PYTHON_TEST_SCRIPT="scripts/socket_load_test.py"
K6_SCRIPT="tests/load/meeting_transcription_test.js"
REPORT_DIR="reports/performance"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT_FILE="$REPORT_DIR/performance_report_$TIMESTAMP.txt"
SOCKET_URL="ws://localhost:$PORT"
# ----------------

# --- Create report directory if not exists ---
mkdir -p "$REPORT_DIR"

# --- Header ---
echo "===============================================" | tee -a "$REPORT_FILE"
echo "🧠 MINA PERFORMANCE VALIDATION RUN" | tee -a "$REPORT_FILE"
echo "Timestamp: $TIMESTAMP" | tee -a "$REPORT_FILE"
echo "===============================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# --- Step 1: Start backend ---
echo "🚀 Starting Mina backend with Gunicorn (port $PORT)..." | tee -a "$REPORT_FILE"
gunicorn -k eventlet -w 1 -b 0.0.0.0:$PORT app:app > "$REPORT_DIR/backend_$TIMESTAMP.log" 2>&1 &
GUNICORN_PID=$!
sleep 5  # wait for backend to boot

if ps -p $GUNICORN_PID > /dev/null; then
    echo "✅ Backend started successfully (PID $GUNICORN_PID)" | tee -a "$REPORT_FILE"
else
    echo "❌ Backend failed to start. Check backend log at $REPORT_DIR/backend_$TIMESTAMP.log" | tee -a "$REPORT_FILE"
    exit 1
fi

# --- Step 2: Run Python Socket.IO Load Test ---
echo "" | tee -a "$REPORT_FILE"
echo "-----------------------------------------------" | tee -a "$REPORT_FILE"
echo "🧩 Running Python Socket.IO Load Test..." | tee -a "$REPORT_FILE"
echo "-----------------------------------------------" | tee -a "$REPORT_FILE"

python $PYTHON_TEST_SCRIPT --url $SOCKET_URL 2>&1 | tee -a "$REPORT_FILE"

# --- Step 3: Run k6 Stress Test ---
echo "" | tee -a "$REPORT_FILE"
echo "-----------------------------------------------" | tee -a "$REPORT_FILE"
echo "📊 Running k6 Stress Test..." | tee -a "$REPORT_FILE"
echo "-----------------------------------------------" | tee -a "$REPORT_FILE"

SOCKET_URL=$SOCKET_URL k6 run $K6_SCRIPT 2>&1 | tee -a "$REPORT_FILE"

# --- Step 4: Cleanup ---
echo "" | tee -a "$REPORT_FILE"
echo "🧹 Cleaning up background processes..." | tee -a "$REPORT_FILE"
kill $GUNICORN_PID
sleep 2

echo "✅ Gunicorn stopped. Logs saved to $REPORT_DIR/backend_$TIMESTAMP.log" | tee -a "$REPORT_FILE"

# --- Step 5: Summary ---
echo "" | tee -a "$REPORT_FILE"
echo "===============================================" | tee -a "$REPORT_FILE"
echo "✅ PERFORMANCE RUN COMPLETE" | tee -a "$REPORT_FILE"
echo "Results saved to: $REPORT_FILE" | tee -a "$REPORT_FILE"
echo "===============================================" | tee -a "$REPORT_FILE"