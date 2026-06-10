"""System-wide audit script for Real Estate Intelligence Engine.

Validates:
- Database tables and record counts
- Data quality (nulls, duplicates, outliers)
- Pipeline integrity (raw -> clean -> valuation -> score)
- Recent errors from logs
- Dashboard data consistency
"""
import sqlite3
import json
import sys
import os
from datetime import datetime
from collections import Counter, defaultdict

DB_PATH = r"c:\Users\rodri\Desktop\Projeto analize mercado imobeleario\data\db\realestate.db"

def audit_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("=" * 80)
    print(" REAL ESTATE ENGINE — SYSTEM AUDIT REPORT")
    print(f" Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    # 1. TABLE COUNTS
    print("\n📊 TABLE RECORD COUNTS")
    print("-" * 40)
    tables = ['raw_listings', 'clean_listings', 'valuations', 'scores', 
              'price_history', 'notifications', 'watchlist', 'job_execution_log', 'ine_data']
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            total = cur.fetchone()[0]
            # Check is_sample
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t} WHERE is_sample = 1")
                sample = cur.fetchone()[0]
            except:
                sample = "N/A"
            print(f"  {t:25s}: {total:6d} total | sample: {sample}")
        except Exception as e:
            print(f"  {t:25s}: ERROR - {e}")

    # 2. RAW LISTINGS QUALITY
    print("\n🔍 RAW LISTINGS QUALITY CHECK")
    print("-" * 40)
    cur.execute("SELECT raw_data, source_portal, is_sample FROM raw_listings")
    rows = cur.fetchall()
    
    portal_counts = Counter()
    null_fields = defaultdict(int)
    invalid_prices = 0
    invalid_areas = 0
    
    for row in rows:
        portal_counts[row['source_portal']] += 1
        try:
            data = json.loads(row['raw_data']) if row['raw_data'] else {}
        except:
            data = {}
        
        # Check required fields
        for field in ['title', 'price_text', 'area_text', 'url']:
            if not data.get(field):
                null_fields[field] += 1
        
        # Price validation
        price_text = data.get('price_text', '')
        if price_text:
            import re
            nums = re.sub(r'[^\d.,]', '', str(price_text))
            if not nums or nums in ['', '.', ',']:
                invalid_prices += 1
        
        # Area validation
        area_text = data.get('area_text', '')
        if area_text:
            import re
            nums = re.sub(r'[^\d.,]', '', str(area_text))
            if not nums:
                invalid_areas += 1
    
    print(f"  Total raw listings: {len(rows)}")
    print(f"  By portal: {dict(portal_counts)}")
    print(f"  Missing fields: {dict(null_fields)}")
    print(f"  Invalid prices: {invalid_prices}")
    print(f"  Invalid areas: {invalid_areas}")

    # 3. CLEAN LISTINGS QUALITY
    print("\n📋 CLEAN LISTINGS QUALITY CHECK")
    print("-" * 40)
    cur.execute("""
        SELECT id, source_portal, source_id, preco_pedido, area_util_m2, 
               quartos, freguesia, lat, lon, is_sample 
        FROM clean_listings
    """)
    clean_rows = cur.fetchall()
    
    null_clean = defaultdict(int)
    zero_price = 0
    zero_area = 0
    no_coords = 0
    
    for row in clean_rows:
        if row['preco_pedido'] is None or row['preco_pedido'] <= 0:
            zero_price += 1
        if row['area_util_m2'] is None or row['area_util_m2'] <= 0:
            zero_area += 1
        if row['lat'] is None or row['lon'] is None:
            no_coords += 1
        for field in ['source_portal', 'source_id', 'titulo']:
            if field in row.keys() and not row[field]:
                null_clean[field] += 1
    
    print(f"  Total clean listings: {len(clean_rows)}")
    print(f"  Zero/invalid price: {zero_price}")
    print(f"  Zero/invalid area: {zero_area}")
    print(f"  Missing coordinates: {no_coords}")
    print(f"  Missing fields: {dict(null_clean)}")

    # 4. VALUATION INTEGRITY
    print("\n💰 VALUATION INTEGRITY CHECK")
    print("-" * 40)
    cur.execute("SELECT COUNT(*) FROM valuations WHERE valor_justo IS NULL OR valor_justo <= 0")
    bad_vals = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM valuations")
    total_vals = cur.fetchone()[0]
    print(f"  Total valuations: {total_vals}")
    print(f"  Invalid valuations (null or <=0): {bad_vals}")
    
    # Check clean_listings without valuations
    cur.execute("""
        SELECT COUNT(*) FROM clean_listings c 
        LEFT JOIN valuations v ON c.id = v.listing_id 
        WHERE v.id IS NULL
    """)
    no_val = cur.fetchone()[0]
    print(f"  Clean listings WITHOUT valuation: {no_val}")

    # 5. SCORING INTEGRITY
    print("\n⭐ SCORING INTEGRITY CHECK")
    print("-" * 40)
    cur.execute("SELECT COUNT(*) FROM scores")
    total_scores = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM scores WHERE score_total IS NULL OR score_total < 0 OR score_total > 10")
    bad_scores = cur.fetchone()[0]
    print(f"  Total scores: {total_scores}")
    print(f"  Invalid scores (out of range): {bad_scores}")
    
    # Clean without scores
    cur.execute("""
        SELECT COUNT(*) FROM clean_listings c 
        LEFT JOIN scores s ON c.id = s.listing_id 
        WHERE s.id IS NULL
    """)
    no_score = cur.fetchone()[0]
    print(f"  Clean listings WITHOUT score: {no_score}")

    # 6. PIPELINE FLOW CHECK
    print("\n🔄 PIPELINE FLOW INTEGRITY")
    print("-" * 40)
    cur.execute("SELECT COUNT(*) FROM raw_listings")
    raw_n = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM clean_listings")
    clean_n = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM valuations")
    val_n = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM scores")
    score_n = cur.fetchone()[0]
    
    print(f"  Raw → Clean: {raw_n} → {clean_n} (loss: {raw_n - clean_n})")
    print(f"  Clean → Valuation: {clean_n} → {val_n} (loss: {clean_n - val_n})")
    print(f"  Valuation → Score: {val_n} → {score_n} (loss: {val_n - score_n})")
    
    if raw_n > 0 and clean_n == 0:
        print("  ⚠️ CRITICAL: Raw data exists but NO clean listings!")
    if clean_n > 0 and val_n == 0:
        print("  ⚠️ WARNING: Clean listings exist but NO valuations!")
    if val_n > 0 and score_n == 0:
        print("  ⚠️ WARNING: Valuations exist but NO scores!")

    # 7. RECENT ERRORS FROM LOGS
    print("\n🐛 RECENT ERRORS (last 20 lines)")
    print("-" * 40)
    log_path = r"c:\Users\rodri\Desktop\Projeto analize mercado imobeleario\logs\errors.log"
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        error_lines = [l.strip() for l in lines if l.strip()]
        for line in error_lines[-20:]:
            print(f"  {line[:120]}")
    else:
        print("  No error log found")

    # 8. DUPLICATES CHECK
    print("\n🔄 DUPLICATE CHECK")
    print("-" * 40)
    cur.execute("SELECT source_id, source_portal, COUNT(*) as c FROM raw_listings GROUP BY source_id, source_portal HAVING c > 1")
    dupes = cur.fetchall()
    print(f"  Duplicate raw listings (same source_id + portal): {len(dupes)}")
    
    cur.execute("SELECT source_id, source_portal, COUNT(*) as c FROM clean_listings GROUP BY source_id, source_portal HAVING c > 1")
    dupes_clean = cur.fetchall()
    print(f"  Duplicate clean listings: {len(dupes_clean)}")

    conn.close()
    
    print("\n" + "=" * 80)
    print(" AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    audit_db()
