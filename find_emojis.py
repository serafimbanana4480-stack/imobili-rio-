import re
import os

emoji_pattern = re.compile(
    '['
    '\U0001F600-\U0001F64F'
    '\U0001F300-\U0001F5FF'
    '\U0001F680-\U0001F6FF'
    '\U0001F700-\U0001F77F'
    '\U0001F780-\U0001F7FF'
    '\U0001F800-\U0001F8FF'
    '\U0001F900-\U0001F9FF'
    '\U0001FA00-\U0001FA6F'
    '\U0001FA70-\U0001FAFF'
    '\U00002702-\U000027B0'
    '\U000024C2-\U0001F251'
    ']+', flags=re.UNICODE)

views_dir = 'realestate_engine/dashboard/views'
for fname in sorted(os.listdir(views_dir)):
    if fname.endswith('.py'):
        path = os.path.join(views_dir, fname)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        emojis_found = []
        for i, line in enumerate(lines, 1):
            matches = emoji_pattern.findall(line)
            if matches:
                for m in matches:
                    emojis_found.append((i, m, line.strip()))
        if emojis_found:
            print(f'\n=== {fname} ===')
            for ln, em, txt in emojis_found:
                print(f'  L{ln}: {em!r} -> {txt[:120]}')
