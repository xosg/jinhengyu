"""Demo script to show what the progress output will look like"""
import time
from datetime import datetime

print("\n" + "="*80)
print("FILE WATCHER PROGRESS OUTPUT DEMO")
print("="*80)
print("\nThis is what you'll see in real-time when files change:\n")

# Simulate file detection
print(f"[{datetime.now().strftime('%H:%M:%S')}] [DETECT] example_file.txt (created)")
time.sleep(0.1)

# Simulate debounce
print(f"[{datetime.now().strftime('%H:%M:%S')}] [WAIT] Batching changes (waiting 2.0s)...")
time.sleep(2)

# Simulate processing
print(f"[{datetime.now().strftime('%H:%M:%S')}] [PROCESS] 1 file(s): example_file.txt")

# Simulate email sending
print(f"[{datetime.now().strftime('%H:%M:%S')}] [EMAIL] Sending to h.jin@student.xu-university.de...")
print(f"[{datetime.now().strftime('%H:%M:%S')}]         Connecting to SMTP server...")
time.sleep(4)  # Simulate SMTP delay

# Simulate success
print(f"[{datetime.now().strftime('%H:%M:%S')}] [SUCCESS] Email sent! (1 file(s) attached)")
print()

print("="*80)
print("Total time: ~6 seconds (2s debounce + 4s SMTP)")
print("You'll know exactly what's happening at each step!")
print("="*80)
