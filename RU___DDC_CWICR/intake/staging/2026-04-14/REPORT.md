# Intake Report — 2026-04-14

## Received files
- `Праи_с-лист---0fe98028-58b2-4ac3-8011-9f9e3d02d12a.pdf`
- `Праи_с-лист---3c228fc7-83fd-4a31-8dbc-845df6b79ea1.pdf`
- `Праи_с-лист_04.08.2022---47459300-ef49-41e1-be1f-77a59fdbe49a` (Apple Numbers)

## Processing completed
1. PDF -> TXT (`pdftotext -layout`)
2. Heuristic extraction TXT -> CSV via:
   - `scripts/ru_regions/extract_price_list_from_pdf.py`
3. Draft extracted catalog:
   - `price_list_extracted.csv`

## Extraction summary
- Parsed rows: **664**
- Currency normalized to: **RUB**
- Units extracted as-is (`м2`, `м.п.`, `шт.`, `компл.` and others)

## Notes
- The extracted CSV is a **draft intake layer** (before semantic mapping to DDC-CWICR catalog entries).
- Some wrapped OCR/PDF lines are noisy and require cleanup during normalization.
- City tag is not inferred automatically yet; assign city explicitly before publishing regional catalog.
