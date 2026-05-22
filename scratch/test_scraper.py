import asyncio
import json
from realestate_engine.scraping.spiders.casa_sapo_direct_spider import CasaSapoDirectSpider

async def main():
    print("Iniciando extração de teste (Casa Sapo)...")
    spider = CasaSapoDirectSpider()
    # Scrape only 1 page for speed
    results = await spider.run(max_pages=1)
    
    print("\n" + "="*50)
    print(f"SUCESSO: Extraídos {len(results)} imóveis.")
    print("="*50 + "\n")
    
    for i, r in enumerate(results[:3]): # Show first 3
        data = r["raw_data"]
        print(f"--- IMÓVEL {i+1} ---")
        print(f"ID: {r['source_id']}")
        print(f"Título: {data['title']}")
        print(f"Preço: {data['preco_pedido']} €")
        print(f"Área: {data['area_util_m2']} m2")
        print(f"Tipologia: {data['rooms_text']}")
        print(f"Localização: {data['location']}")
        print(f"GPS: {data['lat']}, {data['lon']}")
        print(f"URL: {r['source_url']}")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(main())
