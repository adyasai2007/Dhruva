import json

# Let's inspect the remaining 29 places (excluding row 0 / ananta-vasudeva-temple)
with open('data/scraped/normalized_places.json', 'r', encoding='utf-8') as f:
    places = json.load(f)

# Exclude row 0 (ananta-vasudeva-temple)
cleaned_places = places[1:]

print(f"Places count after removing row 0: {len(cleaned_places)}")
for p in cleaned_places:
    # Filter image urls to find Scene7 images
    scene7_imgs = [img for img in p.get('image_urls', []) if 'scene7.com' in img and 'placeholder' not in img]
    print(f"ID: {p['id']} | City: {p['city']} | Timing: {p['opening_hours']} | Scene7: {scene7_imgs[:1]}")
