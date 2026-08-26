import json
import csv

with open('data/scraped/normalized_places.json', 'r', encoding='utf-8') as f:
    places = json.load(f)

print(f"Total entries: {len(places)}")
for i, p in enumerate(places):
    print(f"\n--- Place [{i}] {p['id']} ({p['name']}) City: {p['city']} ---")
    print(f"Category: {p.get('category')} | Subcat: {p.get('sub_category')}")
    print(f"Opening hours: {p.get('opening_hours')}")
    print(f"Duration: {p.get('recommended_duration')}")
    print(f"Festivals: {p.get('festivals')}")
    print("Images:")
    for img in p.get('image_urls', []):
        print(f"   {img}")
