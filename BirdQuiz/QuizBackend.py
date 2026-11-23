"""Browser-backed Macaulay Library image search for BirdQuiz."""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from queue import Queue
from random import choice, sample, shuffle
from threading import Event, Thread
import re
import time
from urllib.parse import urlencode

import requests
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager


BASE_DIR = Path(__file__).resolve().parent
RESOURCE_DIR = BASE_DIR / "resources"
MAX_MEDIA_PER_SPECIES = 5


@dataclass
class MediaRecord:
    image: Image.Image
    species_name: str = ""
    page_url: str = ""
    catalog_number: str = ""
    contributor: str = ""
    source_url: str = ""


class QuizFetchError(RuntimeError):
    """A readable error encountered while preparing quiz images."""


class QuizBackend:
    """Prepare a randomly sampled quiz using one browser worker."""

    def __init__(self, questions=30, download=False, from_file=False,
                 begin_month=9, end_month=2, begin_year=2016, end_year=2025,
                 no_browser=False, taxonomy_records=None):
        self.alpha_species = self._load_default_species()
        self.species: list[str] = []
        self.imgs: list[Image.Image | None] = []
        self.media_records: list[MediaRecord | None] = []
        self.guesses: list[str] = []
        self.outcomes: list[str | None] = []

        self.download = download
        self.from_file = from_file
        self.no_browser = no_browser
        self.questions = questions
        self.i = 0
        self.begin_month = begin_month
        self.end_month = end_month
        self.begin_year = begin_year
        self.end_year = end_year
        self.taxonomy_records = taxonomy_records or self._load_taxonomy_records()

        self.browser = None
        self.fetch_thread = None
        self.status_queue: Queue = Queue()
        self._cancel = Event()
        self._transform_black_white = False
        self.missing_species: list[str] = []

    @staticmethod
    def _load_default_species() -> list[str]:
        species_file = BASE_DIR / "species.txt"
        if not species_file.is_file():
            return []
        with species_file.open("r", encoding="utf-8-sig") as source:
            return sorted({line.strip() for line in source if line.strip()},
                          key=str.casefold)

    @staticmethod
    def _load_taxonomy_records() -> dict[str, dict[str, str]]:
        for filename in (
            "eBird_Taxonomy_v2026.csv",
            "eBird_taxonomy_v2024.csv",
            "ebird_taxonomy_v2023.csv",
        ):
            path = RESOURCE_DIR / filename
            if not path.is_file():
                continue
            import csv
            records = {}
            with path.open("r", encoding="utf-8-sig", newline="") as source:
                for row in csv.DictReader(source):
                    normalized = {
                        (key or "").strip().casefold(): (value or "").strip()
                        for key, value in row.items()
                    }
                    common = normalized.get("primary_com_name", "")
                    if common:
                        records[QuizBackend._normalize(common)] = {
                            "common_name": common,
                            "scientific_name": normalized.get("sci_name", ""),
                            "species_code": normalized.get("species_code", ""),
                        }
            if records:
                return records
        return {}

    @staticmethod
    def _normalize(name: str) -> str:
        return " ".join((name or "").split()).casefold()

    @property
    def correct(self) -> int:
        return sum(outcome == "correct" for outcome in self.outcomes)

    @property
    def counted_questions(self) -> int:
        return sum(outcome in ("correct", "wrong") for outcome in self.outcomes)

    @property
    def uncounted_questions(self) -> int:
        return sum(outcome in ("skipped", "excluded") for outcome in self.outcomes)

    def add_black_white(self):
        self._transform_black_white = True

    def get_current(self):
        if not 0 <= self.i < len(self.imgs) or self.imgs[self.i] is None:
            return None
        image = self.imgs[self.i]
        return image.convert("L") if self._transform_black_white else image

    def get_current_media(self) -> MediaRecord | None:
        if not 0 <= self.i < len(self.media_records):
            return None
        return self.media_records[self.i]

    def get_species(self):
        if not 0 <= self.i < len(self.species):
            return ""
        return self.species[self.i]

    def check(self, answer: str) -> bool:
        if not 0 <= self.i < len(self.species):
            return False
        is_correct = self._normalize(answer) == self._normalize(self.species[self.i])
        self.guesses[self.i] = answer.strip()
        self.outcomes[self.i] = "correct" if is_correct else "wrong"
        return is_correct

    def skip_current(self):
        if 0 <= self.i < len(self.outcomes):
            self.guesses[self.i] = ""
            self.outcomes[self.i] = "skipped"

    def exclude_current(self):
        if 0 <= self.i < len(self.outcomes):
            self.outcomes[self.i] = "excluded"

    def next_species(self):
        self.i += 1

    def begin_thread(self):
        """Start preparing the random quiz without blocking Tkinter."""
        if self.fetch_thread and self.fetch_thread.is_alive():
            return
        if not self.alpha_species:
            raise QuizFetchError("Add at least one valid species before starting.")
        if self.questions < 1:
            raise QuizFetchError("The quiz must contain at least one question.")

        self._cancel.clear()
        self.i = 0
        # Draw independently with replacement; caching does not alter the odds.
        self.species = [choice(self.alpha_species) for _ in range(self.questions)]
        self.imgs = [None] * self.questions
        self.media_records = [None] * self.questions
        self.guesses = [""] * self.questions
        self.outcomes = [None] * self.questions
        self.missing_species = []
        self.fetch_thread = Thread(target=self.fetch_until_stop, daemon=True)
        self.fetch_thread.start()

    def fetch_until_stop(self):
        """Search once per distinct drawn species, then assign its photo pool."""
        requested_draws = list(self.species)
        requested_species = list(dict.fromkeys(requested_draws))
        needed = {
            name: min(requested_draws.count(name), MAX_MEDIA_PER_SPECIES)
            for name in requested_species
        }
        pools: dict[str, list[MediaRecord]] = {name: [] for name in requested_species}
        bags: dict[str, list[MediaRecord]] = {name: [] for name in requested_species}
        available: list[str] = []
        unresolved: list[int] = []
        errors: list[str] = []

        def record_loaded(species_name, record):
            """Publish each image as soon as it downloads, without waiting for a batch."""
            if self._cancel.is_set():
                return
            if (
                record.species_name
                and self._normalize(record.species_name) != self._normalize(species_name)
            ):
                raise QuizFetchError(
                    f"A photo for {record.species_name} was returned while searching for {species_name}."
                )
            record.species_name = species_name
            pools[species_name].append(record)
            bags[species_name].append(record)
            if species_name not in available:
                available.append(species_name)

            # Assign one matching question immediately. The remaining questions
            # for this species are filled as more photos arrive or after search.
            index = next((
                idx for idx, requested_name in enumerate(requested_draws)
                if requested_name == species_name and self.media_records[idx] is None
            ), None)
            if index is not None:
                self._assign_media(index, species_name, pools, bags)
            while unresolved and available:
                index = unresolved.pop(0)
                self._assign_media(index, choice(available), pools, bags)

        try:
            if not self.from_file and not self.no_browser:
                self.open_browser()

            for species_name in requested_species:
                if self._cancel.is_set():
                    raise QuizFetchError("Quiz preparation was cancelled.")
                self.status_queue.put(
                    ("status", f"Searching Macaulay Library for {species_name}…")
                )
                try:
                    if self.from_file:
                        records = self.get_images_from_file(
                            species_name, needed[species_name],
                            on_record=lambda record, name=species_name: record_loaded(name, record),
                        )
                    else:
                        records = self.get_images(
                            species_name, needed[species_name],
                            on_record=lambda record, name=species_name: record_loaded(name, record),
                        )
                except Exception as exc:
                    records = []
                    errors.append(f"{species_name}: {str(exc).strip()}")
                    self.status_queue.put((
                        "status", f"Could not load {species_name}; continuing the quiz."
                    ))
                if pools[species_name]:
                    # If fewer photos exist than questions for this species,
                    # reuse its own pool before considering substitutions.
                    for index, requested_name in enumerate(requested_draws):
                        if requested_name == species_name and self.media_records[index] is None:
                            self._assign_media(index, species_name, pools, bags)
                    while unresolved and available:
                        index = unresolved.pop(0)
                        self._assign_media(index, choice(available), pools, bags)
                else:
                    self.missing_species.append(species_name)
                    unresolved.extend(
                        index for index, requested_name in enumerate(requested_draws)
                        if requested_name == species_name
                    )

            if not available:
                names = ", ".join(self.missing_species) or "the selected species"
                detail = f" Details: {errors[0]}" if errors else ""
                raise QuizFetchError(f"No usable photos were found for {names}.{detail}")

            for index in unresolved:
                self._assign_media(index, choice(available), pools, bags)

            assigned_media = [record for record in self.media_records if record]
            assigned_species = [
                name for name, record in zip(self.species, self.media_records) if record
            ]
            if self.download:
                self._save_images(assigned_media, assigned_species)
            replacement_count = sum(
                requested != actual
                for requested, actual in zip(requested_draws, self.species)
            )
            self.status_queue.put(("complete", {
                "missing_species": list(self.missing_species),
                "replacement_count": replacement_count,
                "warning": errors[0] if errors else "",
            }))
        except Exception as exc:
            message = str(exc).strip() or exc.__class__.__name__
            # A later species can fail after the first question is already on
            # screen. Finish from the photos already loaded so the UI cannot
            # get stuck with unassigned questions.
            if available and not self._cancel.is_set():
                for index, record in enumerate(self.media_records):
                    if record is None:
                        replacement = choice(available)
                        self._assign_media(index, replacement, pools, bags)
                self.status_queue.put(("complete", {
                    "missing_species": list(self.missing_species),
                    "replacement_count": sum(
                        requested != actual
                        for requested, actual in zip(requested_draws, self.species)
                    ),
                    "warning": message,
                }))
            else:
                self.status_queue.put(("error", message))
        finally:
            if self.browser is not None:
                try:
                    self.browser.quit()
                except WebDriverException:
                    pass
                self.browser = None

    def _assign_media(self, index, species_name, pools, bags):
        if self.media_records[index] is not None:
            return
        bag = bags[species_name]
        if not bag:
            bag.extend(pools[species_name])
            shuffle(bag)
        record = bag.pop()
        if (
            record.species_name
            and self._normalize(record.species_name) != self._normalize(species_name)
        ):
            raise QuizFetchError(
                f"Refusing to assign a {record.species_name} photo to {species_name}."
            )
        self.species[index] = species_name
        self.media_records[index] = record
        self.imgs[index] = record.image
        self.status_queue.put(("question_ready", index))

    def _save_images(self, records, species_names):
        for record, species_name in zip(records, species_names):
            record_species = record.species_name or species_name
            if self._normalize(record_species) != self._normalize(species_name):
                raise QuizFetchError(
                    f"Refusing to save a {record_species} photo in the {species_name} folder."
                )
            folder = BASE_DIR / "Quizzes" / record_species
            folder.mkdir(parents=True, exist_ok=True)
            filename = f"{time.time_ns()}.jpg"
            record.image.convert("RGB").save(folder / filename, format="JPEG")

    def open_browser(self):
        """Open a visible Chrome window so a user can complete site verification."""
        options = Options()
        options.add_argument("--start-maximized")
        driver_path = ChromeDriverManager(
            cache_manager=DriverCacheManager(root_dir=str(RESOURCE_DIR))
        ).install()
        self.browser = webdriver.Chrome(service=Service(driver_path), options=options)
        self.browser.set_page_load_timeout(45)

    def _is_verification_page(self) -> bool:
        if self.browser is None:
            return False
        try:
            url = (self.browser.current_url or "").casefold()
            page_text = (
                self.browser.find_element(By.TAG_NAME, "body").text or ""
            ).casefold()
        except WebDriverException:
            return False
        return (
            "/.within.website/x/" in url
            or "making sure you're not a bot" in page_text
            or "verify you are human" in page_text
            or "checking your browser" in page_text
            or "proof-of-work challenge" in page_text
        )

    def _wait_for_verification(self, timeout=180):
        if not self._is_verification_page():
            return
        self.status_queue.put((
            "status",
            "Complete the verification in the Chrome window. The quiz will continue afterward.",
        ))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._cancel.is_set():
                raise QuizFetchError("Quiz preparation was cancelled.")
            if not self._is_verification_page():
                return
            time.sleep(0.4)
        raise QuizFetchError("Browser verification was not completed before the timeout.")

    def _month_values(self) -> list[int]:
        start = int(self.begin_month)
        end = int(self.end_month)
        if not 1 <= start <= 12 or not 1 <= end <= 12:
            raise QuizFetchError("Months must be between 1 and 12.")
        if start <= end:
            return list(range(start, end + 1))
        return list(range(start, 13)) + list(range(1, end + 1))

    def _search_periods(self) -> list[dict[str, int]]:
        """Return one broad range so each unique species needs one search."""
        self._month_values()  # Validate the configured month range.
        first_year, last_year = sorted(
            (int(self.begin_year), int(self.end_year))
        )
        return [{
            "date.beginMonth": int(self.begin_month),
            "date.endMonth": int(self.end_month),
            "date.beginYear": first_year,
            "date.endYear": last_year,
        }]

    def get_images(self, species_name: str, num_imgs: int = 1,
                   on_record=None) -> list[MediaRecord]:
        if self.browser is None:
            raise QuizFetchError("The browser was not initialized.")
        records = []
        seen = set()
        for period in self._search_periods():
            cards = self.search_bird(species_name, period, num_imgs)
            if cards:
                def keep_record(record):
                    identity = record.catalog_number or record.source_url or record.page_url
                    if identity and identity in seen:
                        return False
                    if identity:
                        seen.add(identity)
                    records.append(record)
                    if on_record:
                        on_record(record)
                    return True

                self.load_imgs(
                    cards, num_imgs - len(records), species_name, keep_record
                )
                if len(records) >= num_imgs:
                    return records
            if self._cancel.is_set():
                break
        return records

    def search_bird(self, species_name: str, period=None, needed=1,
                    verification_retry=0):
        """Open the species-filtered catalog URL and return its result cards."""
        taxon = self.taxonomy_records.get(self._normalize(species_name))
        if not taxon or not taxon.get("scientific_name"):
            raise QuizFetchError(
                f"No scientific name is available for {species_name} in the local taxonomy."
            )
        params = {
            "view": "grid",
            "mediaType": "photo",
            "searchField": "species",
            "species": f"{taxon['common_name']} - {taxon['scientific_name']}",
        }
        if period:
            params.update(period)
        self.browser.get(f"https://media.ebird.org/catalog?{urlencode(params)}")
        self._wait_for_verification()
        expected_species = (
            self._normalize(taxon["common_name"]),
            self._normalize(taxon["scientific_name"]),
        )
        try:
            WebDriverWait(self.browser, 20, poll_frequency=0.4).until(
                lambda driver: self._matching_result_cards(expected_species)
                or self._page_has_no_results()
            )
        except TimeoutException:
            if self._is_verification_page():
                self._wait_for_verification()
                if verification_retry < 1:
                    return self.search_bird(
                        species_name, period, needed, verification_retry + 1
                    )
            return []

        # Use the first result page immediately. Waiting to expand the full
        # result set before downloading anything delays question 1 needlessly.
        return self._matching_result_cards(expected_species)

    def _page_has_no_results(self) -> bool:
        try:
            text = self.browser.find_element(By.TAG_NAME, "body").text.casefold()
        except WebDriverException:
            return False
        return "no results" in text or "no media found" in text

    def _matching_result_cards(self, expected_species):
        matches = []
        try:
            card_metadata = self.browser.execute_script(
                """
                return Array.from(document.querySelectorAll('.ResultsGrid-card-image'))
                  .map(root => {
                    let card = root;
                    for (let i = 0; i < 8 && card; i++, card = card.parentElement) {
                      const classes = typeof card.className === 'string' ? card.className : '';
                      if (classes.split(String.fromCharCode(32)).includes('ResultsGrid-card')) break;
                    }
                    if (!card) card = root.parentElement || root;
                    const image = root.matches('img') ? root : root.querySelector('img');
                    const text = [card.innerText || ''];
                    const labeled = card.querySelectorAll(
                      '[aria-label], [title], [data-species], [data-scientific-name], [data-taxon]');
                    for (const node of [root, card, ...labeled]) {
                      for (const key of ['aria-label', 'title', 'data-species',
                                          'data-scientific-name', 'data-taxon']) {
                        const value = node.getAttribute && node.getAttribute(key);
                        if (value) text.push(value);
                      }
                    }
                    return {
                      element: root,
                      text: text.join(' '),
                      alt: image ? [image.alt, image.title].filter(Boolean).join(' ') : ''
                    };
                  });
                """
            ) or []
            for item in card_metadata:
                if self._metadata_matches(item, expected_species):
                    matches.append(item["element"])
        except (StaleElementReferenceException, WebDriverException):
            return []
        return matches

    def _card_metadata(self, element) -> dict[str, str]:
        return self.browser.execute_script(
            """
            const root = arguments[0];
            const image = root.matches('img') ? root : root.querySelector('img');
            let card = root;
            for (let i = 0; i < 8 && card; i++, card = card.parentElement) {
              const classes = typeof card.className === 'string' ? card.className : '';
              if (classes.split(String.fromCharCode(32)).includes('ResultsGrid-card')) break;
            }
            if (!card) card = root.parentElement || root;
            const text = [card.innerText || ''];
            const labeled = card.querySelectorAll(
              '[aria-label], [title], [data-species], [data-scientific-name], [data-taxon]');
            for (const node of [root, card, ...labeled]) {
              for (const key of ['aria-label', 'title', 'data-species',
                                  'data-scientific-name', 'data-taxon']) {
                const value = node.getAttribute && node.getAttribute(key);
                if (value) text.push(value);
              }
            }
            const anchor = root.closest('a[href]') || card.querySelector('a[href]');
            const style = getComputedStyle(root);
            const background = style.backgroundImage || '';
            let backgroundUrl = '';
            if (background.startsWith('url(')) {
              backgroundUrl = background.slice(4, -1).trim();
              if ((backgroundUrl.startsWith('"') && backgroundUrl.endsWith('"')) ||
                  (backgroundUrl.startsWith("'") && backgroundUrl.endsWith("'"))) {
                backgroundUrl = backgroundUrl.slice(1, -1);
              }
            }
            return {
              text: text.join(' '),
              alt: image ? [image.alt, image.title].filter(Boolean).join(' ') : '',
              href: anchor ? anchor.href : '',
              source: image ? (image.currentSrc || image.src || image.getAttribute('data-src') || '') : '',
              background: backgroundUrl
            };
            """,
            element,
        ) or {}

    def _metadata_matches(self, metadata, expected_species) -> bool:
        text = self._normalize(" ".join(
            str(metadata.get(key, "")) for key in ("text", "alt")
        ))
        for name in expected_species:
            if not name:
                continue
            if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text):
                return True
        return False

    def load_imgs(self, cards, num_imgs: int = 1, species_name: str = "",
                  on_record=None) -> list[MediaRecord]:
        """Load up to the available cards; sparse results are a normal outcome."""
        if not cards or num_imgs <= 0:
            return []
        taxon = self.taxonomy_records.get(self._normalize(species_name), {})
        expected_species = tuple(
            self._normalize(name)
            for name in (taxon.get("common_name", ""), taxon.get("scientific_name", ""))
            if name
        )
        selected = sample(list(cards), min(num_imgs, len(cards)))
        records = []
        for card in selected:
            try:
                images = card.find_elements(By.TAG_NAME, "img")
                element = images[0] if images else card
                metadata = self._card_metadata(card)
                if expected_species and not self._metadata_matches(metadata, expected_species):
                    continue
                source_url = (
                    metadata.get("source", "")
                    or metadata.get("background", "")
                    or element.get_attribute("src")
                    or element.get_attribute("data-src")
                    or ""
                )
                image = self._download_image(source_url, element)
                if image is None:
                    continue
                text = "\n".join((
                    metadata.get("text", ""),
                    metadata.get("alt", ""),
                    metadata.get("href", ""),
                    source_url,
                ))
                match = re.search(
                    r"(?:/asset/|\bML\s*)(\d{4,})", text, re.IGNORECASE
                )
                catalog_number = f"ML{match.group(1)}" if match else ""
                page_url = metadata.get("href", "") or ""
                if catalog_number:
                    page_url = (
                        f"https://macaulaylibrary.org/asset/{catalog_number[2:]}"
                    )
                contributor = self._extract_contributor(metadata.get("text", ""))
                records.append(MediaRecord(
                    image=image,
                    species_name=species_name,
                    page_url=page_url,
                    catalog_number=catalog_number,
                    contributor=contributor,
                    source_url=source_url,
                ))
                if on_record:
                    on_record(records[-1])
            except (
                NoSuchElementException,
                StaleElementReferenceException,
                WebDriverException,
            ):
                continue
        return records

    @staticmethod
    def _extract_contributor(card_text: str) -> str:
        for line in (card_text or "").splitlines():
            cleaned = line.strip()
            if cleaned.casefold().startswith("by "):
                return cleaned[3:].strip()
        return ""

    @staticmethod
    def _download_image(source_url: str, element) -> Image.Image | None:
        if source_url:
            try:
                response = requests.get(source_url, timeout=20)
                response.raise_for_status()
                return Image.open(BytesIO(response.content)).convert("RGB").copy()
            except (requests.RequestException, OSError, ValueError):
                pass
        try:
            return Image.open(BytesIO(element.screenshot_as_png)).convert("RGB").copy()
        except (WebDriverException, OSError, ValueError):
            return None

    def get_images_from_file(self, species_name: str, num_imgs: int = 1,
                             on_record=None) -> list[MediaRecord]:
        root = BASE_DIR / "Quizzes" / species_name
        if not root.is_dir():
            return []
        files = [path for path in root.iterdir()
                 if path.suffix.casefold() in {".jpg", ".jpeg", ".png", ".webp"}]
        if not files:
            return []
        records = []
        for path in sample(files, min(num_imgs, len(files))):
            try:
                with Image.open(path) as source:
                    record = MediaRecord(
                        image=source.convert("RGB").copy(),
                        species_name=species_name,
                    )
                    records.append(record)
                    if on_record:
                        on_record(record)
            except (OSError, ValueError):
                continue
        return records

    def cancel(self):
        self._cancel.set()
