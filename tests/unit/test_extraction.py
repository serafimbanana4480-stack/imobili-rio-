import sys
sys.path.insert(0, 'realestate_engine')

from realestate_engine.scraping.spiders.casa_sapo_spider_nodriver import CasaSapoSpider

spider = CasaSapoSpider()

# Test cases
test_texts = [
    "Apartamento T2 em Bonfim com 96 m²",
    "T3 123 m2 Foz do Douro",
    "Apartamento 131sqm",
    "2 quartos 86 m",
    "T4 sem área",
]

print("=" * 80)
print("TESTING EXTRACTION FUNCTIONS")
print("=" * 80)

for text in test_texts:
    area = spider.extract_area_from_text(text)
    rooms = spider.extract_rooms_from_text(text)
    print(f"Text: '{text}'")
    print(f"  Area: '{area}'")
    print(f"  Rooms: '{rooms}'")
    print()
