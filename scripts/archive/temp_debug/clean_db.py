import sqlite3
import json

conn = sqlite3.connect('data/db/realestate.db')
cursor = conn.cursor()

# Check current state
cursor.execute('SELECT COUNT(*) FROM raw_listings')
total_raw = cursor.fetchone()[0]
print(f"Total raw listings before cleanup: {total_raw}")

# Delete raw listings with empty area_text
cursor.execute('''
    DELETE FROM raw_listings 
    WHERE json_extract(raw_data, '$.area_text') IS NULL 
    OR json_extract(raw_data, '$.area_text') = ''
    OR json_extract(raw_data, '$.area_text') = ' '
''')
deleted_raw = cursor.rowcount
print(f"Deleted {deleted_raw} raw listings with empty areas")

# Also delete from clean_listings to start fresh
cursor.execute('DELETE FROM clean_listings')
deleted_clean = cursor.rowcount
print(f"Deleted {deleted_clean} clean listings")

conn.commit()

# Check final state
cursor.execute('SELECT COUNT(*) FROM raw_listings')
total_raw_after = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM clean_listings')
total_clean_after = cursor.fetchone()[0]

print(f"\nTotal raw listings after cleanup: {total_raw_after}")
print(f"Total clean listings after cleanup: {total_clean_after}")

conn.close()
print("\nDatabase cleanup completed!")
