import csv

from config import CSV_FIELDS


def export_to_csv(leads: list[dict], output_path: str) -> None:
    """Exporte une liste de leads vers un fichier CSV."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            row = {field: lead.get(field, "") for field in CSV_FIELDS}
            writer.writerow(row)
    print(f"[+] {len(leads)} leads exportés vers {output_path}")
