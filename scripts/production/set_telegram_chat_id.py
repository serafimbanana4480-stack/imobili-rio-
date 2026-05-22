"""Script para configurar Chat ID no .env."""
import os

chat_id = "6052459447"
env_path = ".env"

# Read .env
lines = []
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

# Update or add TELEGRAM_CHAT_ID
updated = False
for i, line in enumerate(lines):
    if line.strip().startswith("TELEGRAM_CHAT_ID="):
        lines[i] = f'TELEGRAM_CHAT_ID="{chat_id}"\n'
        updated = True
        break

if not updated:
    lines.append(f'TELEGRAM_CHAT_ID="{chat_id}"\n')

# Write back
with open(env_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"✅ Chat ID {chat_id} configurado no .env")
