import json
from datetime import datetime

lines = open('logs/collection_log.jsonl', 'r', encoding='utf-8').readlines()
logs = [json.loads(l) for l in lines[-5:]]

print('=== Timing Analysis ===\n')
detection_time = None
process_time = None

for log in logs:
    ts = log['timestamp']
    action = log['action']
    status = log['status']

    if 'file_change' in action and 'detected' in status:
        if detection_time is None:
            detection_time = datetime.fromisoformat(ts)
            print(f'1. File detected:     {ts}')

    elif 'process_changes' in action:
        process_time = datetime.fromisoformat(ts)
        delay1 = (process_time - detection_time).total_seconds()
        print(f'2. Processing start:  {ts}  (+{delay1:.2f}s debounce delay)')

    elif 'send_notification' in action:
        send_time = datetime.fromisoformat(ts)
        delay2 = (send_time - process_time).total_seconds()
        total = (send_time - detection_time).total_seconds()
        print(f'3. Email sent:        {ts}  (+{delay2:.2f}s SMTP time)')
        print(f'\n>>> Total time (file created -> email sent): {total:.2f}s')
