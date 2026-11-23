"""Canonical eBird taxonomy lookups for the quiz UI."""

import csv
from pathlib import Path

try:
    from rapidfuzz import fuzz, process
except ImportError:
    fuzz = process = None


RESOURCE_DIR = Path(__file__).resolve().parent / "resources"
TAXONOMY_FILES = (
    "eBird_Taxonomy_v2026.csv",
    "eBird_taxonomy_v2024.csv",
    "ebird_taxonomy_v2023.csv",
)


def normalize_name(name: str) -> str:
    """Normalize names for case-insensitive matching without changing display text."""
    return " ".join((name or "").split()).casefold()


class Validate:
    """Load one local eBird taxonomy and provide canonical names and suggestions."""

    def __init__(self, taxonomy_path: Path | None = None) -> None:
        self.taxonomy_path = taxonomy_path or self._find_taxonomy()
        self.species_by_key: dict[str, dict[str, str]] = {}
        self.species_set: set[str] = set()
        self._load_taxonomy()

    @staticmethod
    def _find_taxonomy() -> Path:
        for filename in TAXONOMY_FILES:
            path = RESOURCE_DIR / filename
            if path.is_file():
                return path
        expected = ", ".join(TAXONOMY_FILES)
        raise FileNotFoundError(
            f"No eBird taxonomy CSV was found in {RESOURCE_DIR}. "
            f"Expected one of: {expected}"
        )

    def _load_taxonomy(self) -> None:
        with self.taxonomy_path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            for raw_row in reader:
                row = {str(key).strip().casefold(): (value or "").strip()
                       for key, value in raw_row.items() if key}
                common_name = row.get("primary_com_name", "")
                if not common_name:
                    continue
                key = normalize_name(common_name)
                self.species_by_key.setdefault(key, {
                    "common_name": common_name,
                    "scientific_name": row.get("sci_name", ""),
                    "species_code": row.get("species_code", ""),
                    "category": row.get("category", ""),
                })
        self.species_set = {
            record["common_name"] for record in self.species_by_key.values()
        }
        self.species = sorted(self.species_set, key=str.casefold)
        self._display_by_key = {
            normalize_name(species): species for species in self.species
        }
        self._normalized_names = list(self._display_by_key)

    def canonicalize(self, name: str) -> str | None:
        """Return the taxonomy's preferred spelling, or None for an unknown name."""
        record = self.species_by_key.get(normalize_name(name))
        return record["common_name"] if record else None

    def get_record(self, name: str) -> dict[str, str] | None:
        """Return taxonomy metadata for a recognized common name."""
        record = self.species_by_key.get(normalize_name(name))
        return dict(record) if record else None

    def validate(self, name: str) -> bool:
        return self.canonicalize(name) is not None

    def suggest(self, name: str, size: int = 10) -> list[str]:
        query = normalize_name(name)
        if not query or size <= 0:
            return []

        prefix = [species for species in self.species
                  if normalize_name(species).startswith(query)]
        contains = [species for species in self.species
                    if query in normalize_name(species)
                    and species not in prefix]
        results = (prefix + contains)[:size]
        if len(results) < size and len(query) >= 4 and process is not None:
            found = process.extract(
                query,
                self._normalized_names,
                scorer=fuzz.ratio,
                limit=size,
                score_cutoff=55,
            )
            for normalized_name, _score, _index in found:
                species = self._display_by_key[normalized_name]
                if species not in results:
                    results.append(species)
                if len(results) >= size:
                    break
        return results

    def search(self, name: str, max_cost: int = 3, size: int = 10):
        """Compatibility wrapper for the previous list-of-rows autocomplete API."""
        return [[species] for species in self.suggest(name, size=size)]


if __name__ == "__main__":
    validator = Validate()
    print('"Wood Thrush" is valid: ' + str(validator.validate("Wood Thrush")))
    print('"wood thrush" is valid: ' + str(validator.validate("wood thrush")))
    print('Suggestions: ' + str(validator.suggest("wood th")))
