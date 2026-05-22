"""Unified REMAX debugging script with multiple modes.

This script consolidates the functionality of:
- probe_remax.py: Simple URL probe
- debug_remax_direct.py: Direct spider debugging
- debug_remax_html.py: HTML structure analysis
- debug_remax_simple.py: Simple pattern checking

Usage:
    python debug_remax.py probe <url>
    python debug_remax.py direct [limit]
    python debug_remax.py html <url>
    python debug_remax.py simple <url>
"""
import asyncio
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import httpx
from realestate_engine.scraping.spiders.remax_direct_spider import REMAXDirectSpider
from realestate_engine.scraping.http_client import default_headers, pick_user_agent


async def mode_probe(url: str):
    """Simple probe to fetch and analyze a single REMAX URL."""
    print(f"Probing: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        resp = await client.get(url)
        print(f"Status: {resp.status_code}")
        
        with open("remax_detail.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        
        # Look for script tags
        scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        print(f"Found {len(scripts)} script tags")
        
        for i, s in enumerate(scripts):
            if "application/ld+json" in resp.text:  # check outer
                pass
            if "@type" in s:
                print(f"Script {i} contains @type: {s[:100]}...")
            if "__NEXT_DATA__" in s:
                print(f"Script {i} contains __NEXT_DATA__")


async def mode_direct(limit: int = 100):
    """Debug REMAX Direct spider to see why listings are being skipped."""
    print(f"Debugging REMAX Direct spider (limit: {limit})")
    
    spider = REMAXDirectSpider()
    
    headers = default_headers(lang="pt-PT,pt;q=0.9,en;q=0.8")
    timeout = httpx.Timeout(45.0, connect=15.0)
    
    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True, http2=False) as client:
        # Get sitemap
        candidates = await spider._discover_listing_urls(client, limit)
        print(f"Found {len(candidates)} candidate URLs")
        
        if candidates:
            # Test first URL
            test_url = candidates[0]
            print(f"\nTesting URL: {test_url}")
            
            resp = await client.get(test_url, headers={"User-Agent": pick_user_agent()})
            print(f"Status: {resp.status_code}")
            
            # Try to extract JSON-LD
            LD_JSON_RE = re.compile(
                r'<script\b[^>]*type=["\']application/ld(?:\+|&#x2B;)json["\'][^>]*>(.*?)</script>',
                re.DOTALL | re.IGNORECASE,
            )
            
            blocks = LD_JSON_RE.findall(resp.text)
            print(f"Found {len(blocks)} JSON-LD blocks")
            
            for i, block in enumerate(blocks[:3]):
                print(f"\n--- Block {i+1} ---")
                try:
                    data = json.loads(block.strip())
                    print(f"Type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())[:10]}")
                        if "@type" in data:
                            print(f"@type: {data['@type']}")
                    if isinstance(data, list) and len(data) > 0:
                        print(f"First item type: {data[0].get('@type', 'unknown')}")
                        print(f"First item keys: {list(data[0].keys())[:10]}")
                except Exception as e:
                    print(f"Error parsing: {e}")


async def mode_html(url: str):
    """Debug REMAX HTML structure."""
    print(f"Analyzing HTML structure: {url}")
    
    headers = default_headers(lang="pt-PT,pt;q=0.9,en;q=0.8")
    timeout = httpx.Timeout(45.0, connect=15.0)
    
    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True, http2=False) as client:
        resp = await client.get(url, headers={"User-Agent": pick_user_agent()})
        print(f"Status: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")
        
        # Save HTML for inspection
        with open("remax_debug.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        
        # Check for common patterns
        if "__NEXT_DATA__" in resp.text:
            print("✓ Found __NEXT_DATA__")
        if "application/ld+json" in resp.text:
            print("✓ Found application/ld+json")
        if '"price"' in resp.text.lower():
            print("✓ Found price in HTML")
        if '"area"' in resp.text.lower() or '"m²"' in resp.text:
            print("✓ Found area in HTML")
        
        # Look for JSON data
        next_data_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if next_data_match:
            print(f"\n__NEXT_DATA__ found, length: {len(next_data_match.group(1))}")
            # Try to parse it
            try:
                data = json.loads(next_data_match.group(1))
                print(f"Keys: {list(data.keys())}")
                if "props" in data:
                    print(f"props keys: {list(data['props'].keys())}")
            except Exception as e:
                print(f"Error parsing __NEXT_DATA__: {e}")


async def mode_simple(url: str):
    """Simple debug for REMAX page."""
    print(f"Simple debug: {url}")
    
    headers = default_headers(lang="pt-PT,pt;q=0.9,en;q=0.8")
    timeout = httpx.Timeout(45.0, connect=15.0)
    
    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True, http2=False) as client:
        resp = await client.get(url, headers={"User-Agent": pick_user_agent()})
        print(f"Status: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")
        
        # Check for patterns
        print(f"Has __NEXT_DATA__: {'__NEXT_DATA__' in resp.text}")
        print(f"Has ld+json: {'application/ld+json' in resp.text}")
        print(f"Has price: {'price' in resp.text.lower()}")
        print(f"Has euro: {'€' in resp.text}")
        
        # Look for any JSON in script tags
        script_matches = re.findall(r'<script[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        print(f"\nFound {len(script_matches)} script tags")

        for i, script in enumerate(script_matches):
            if 'application/json' in script or 'application/ld' in script or '__NEXT_DATA__' in script:
                print(f"\n--- Script {i} (potential JSON) ---")
                print(f"Length: {len(script)}")
                print(f"Preview: {script[:200]}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_remax.py <mode> [args]")
        print("\nModes:")
        print("  probe <url>          - Simple URL probe")
        print("  direct [limit]       - Direct spider debugging (default limit: 100)")
        print("  html <url>           - HTML structure analysis")
        print("  simple <url>         - Simple pattern checking")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "probe":
        if len(sys.argv) < 3:
            print("Error: probe mode requires URL argument")
            sys.exit(1)
        await mode_probe(sys.argv[2])
    elif mode == "direct":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        await mode_direct(limit)
    elif mode == "html":
        if len(sys.argv) < 3:
            print("Error: html mode requires URL argument")
            sys.exit(1)
        await mode_html(sys.argv[2])
    elif mode == "simple":
        if len(sys.argv) < 3:
            print("Error: simple mode requires URL argument")
            sys.exit(1)
        await mode_simple(sys.argv[2])
    else:
        print(f"Error: Unknown mode '{mode}'")
        print("Available modes: probe, direct, html, simple")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
