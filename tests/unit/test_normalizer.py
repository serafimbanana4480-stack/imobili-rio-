import sys
sys.path.insert(0, 'realestate_engine')

from realestate_engine.etl.normalizer import Normalizer

# Test cases from the database
test_cases = [
    "96 m2",
    "123 m2", 
    "131 m2",
    "86 m2",
    "91 m2",
    # Edge cases
    "96.5 m2",
    "96,5 m2",
    "96 000 m2",  # This might be the problem!
]

print("=" * 80)
print("TESTING NORMALIZER")
print("=" * 80)

for test in test_cases:
    result = Normalizer.normalize_area(test)
    print(f"Input: '{test}' -> Output: {result}")
