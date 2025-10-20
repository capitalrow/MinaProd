"""
Mina WebSocket Concurrency Load Test
Simulates concurrent Socket.IO clients connecting and streaming messages.
Usage:
    python scripts/socket_load_test.py --url ws://localhost:5000/socket.io
"""

import asyncio, socketio, random, time, argparse
from statistics import mean
from rich.console import Console
from rich.table import Table
from faker import Faker

console = Console()
fake = Faker()

# ------------------- Config -------------------
NUM_CLIENTS = 25
MESSAGES_PER_CLIENT = 20
DELAY_BETWEEN_MSG = 0.2  # seconds
# ----------------------------------------------

latencies = []
errors = 0

async def simulate_client(client_id, url):
    global errors
    sio = socketio.AsyncClient()
    start_time = time.perf_counter()

    @sio.event
    async def connect():
        console.log(f"[green]Client {client_id} connected[/green]")
        for i in range(MESSAGES_PER_CLIENT):
            msg = fake.sentence(nb_words=8)
            t0 = time.perf_counter()
            try:
                await sio.emit("transcribe_chunk", {"text": msg, "session_id": f"loadtest-{client_id}"})
                latencies.append((time.perf_counter() - t0) * 1000)
            except Exception as e:
                errors += 1
                console.log(f"[red]Emit failed (client {client_id}): {e}[/red]")
            await asyncio.sleep(DELAY_BETWEEN_MSG)
        await sio.disconnect()

    @sio.event
    async def disconnect():
        duration = (time.perf_counter() - start_time)
        console.log(f"[yellow]Client {client_id} disconnected after {duration:.1f}s[/yellow]")

    try:
        await sio.connect(url, wait_timeout=10)
        await sio.wait()
    except Exception as e:
        console.log(f"[red]Client {client_id} failed to connect: {e}[/red]")
        errors += 1

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Socket.IO server URL (e.g. ws://localhost:5000)")
    args = parser.parse_args()

    console.rule("[bold blue]Starting Mina WebSocket Load Test[/bold blue]")
    start = time.perf_counter()

    tasks = [simulate_client(i, args.url) for i in range(NUM_CLIENTS)]
    await asyncio.gather(*tasks)

    duration = time.perf_counter() - start
    avg_latency = mean(latencies) if latencies else 0

    table = Table(title="Mina Load Test Results")
    table.add_column("Metric"); table.add_column("Value")
    table.add_row("Clients", str(NUM_CLIENTS))
    table.add_row("Messages per client", str(MESSAGES_PER_CLIENT))
    table.add_row("Total messages", str(NUM_CLIENTS * MESSAGES_PER_CLIENT))
    table.add_row("Average latency (ms)", f"{avg_latency:.2f}")
    table.add_row("Errors", str(errors))
    table.add_row("Total duration (s)", f"{duration:.2f}")
    console.print(table)
    console.rule("[green]Test complete[/green]")

if __name__ == "__main__":
    asyncio.run(main())