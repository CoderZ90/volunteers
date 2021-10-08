#!/usr/bin/env python3

import csv
import hashlib
import json
import logging
import requests
import validators
import sys

from collections import defaultdict
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from requests.models import HTTPError

# Set logging level
logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.INFO)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpWu2GwKfZF5VQLFGHWuWiPSk-riYszgiKYocCjAJG0vM1HNSZaJ5uAdUCjWoMcbVn1gWPAx2HNj7B/pub?gid=0&single=true&output=csv"

PRINT_WIDTH = 70

# Paths
OUTPUT_DIR = Path("tmp")
IMAGE_DIR = OUTPUT_DIR / "images"
OUTPUT_JSON = OUTPUT_DIR / "data.json"

PLACEHOLDER_IMAGE_URL = (
    "https://images.assetsdelivery.com/compings_v2/apoev/apoev1901/apoev190100061.jpg"
)

ddict = lambda: defaultdict(ddict)


def get_csv(url):
    response = requests.get(url)
    response.raise_for_status()
    lines = response.text.split("\n")
    return csv.DictReader(lines)


def get_image(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    response.raw.decode_content = True

    image = Image.open(response.raw)

    # Should be a square image
    width, height = image.size
    assert 0.95 < width / height < 1.05

    image = image.resize((256, 256))
    return image.convert("RGB")


def parse_row(row, log_ix):
    row = {k: v.strip() for k, v in row.items()}

    assert len(row["name"]) > 0

    output = ddict()

    for column in ["name", "bio"]:
        output[column] = row[column]

    def validate_url(column):
        if not validators.url(row[column]):
            if row[column]:
                logging.warning(f"R{log_ix}: Invalid {column}")
            return False
        return True

    if validate_url("link"):
        output["link"] = row["link"].lower()

    for column in ["github", "linkedin", "twitter", "instagram"]:
        if validate_url(column):
            output["socials"][column] = row[column].lower()

    if validate_url("image"):
        # Hash of url
        hash = hashlib.md5(row["image"].encode()).hexdigest()
        filepath = IMAGE_DIR / f"{hash}.jpg"
        # Initialize with old image for same link
        if filepath.exists():
            output["image"] = filepath.name
        if fetch_and_write_image(row["image"], filepath, log_ix):
            output["image"] = filepath.name

    return output


def fetch_and_write_image(url, filepath, log_ix=None):
    log_prefix = f'R{log_ix}: ' if log_ix is not None else ''
    try:
        image = get_image(url)
        image.save(filepath)
        return True
    except HTTPError:
        logging.warning(f"{log_prefix}Unable to fetch image - {url}")
    except UnidentifiedImageError:
        logging.warning(f"{log_prefix}Unable to read image - {url}")
    except AssertionError:
        logging.warning(f"{log_prefix}Not a square image - {url}")
    return False


def write_json(data, filepath):
    with open(filepath, "w") as f:
        output = sorted(data, key=lambda x: x["name"])
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    logging.info("-" * PRINT_WIDTH)
    logging.info("FETCH".center(PRINT_WIDTH))

    logging.info("-" * PRINT_WIDTH)
    logging.info("Fetching CSV...")
    logging.info(f"URL: {CSV_URL}")
    reader = get_csv(CSV_URL)
    logging.info("Done!")

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    logging.info("-" * PRINT_WIDTH)
    logging.info("Parsing CSV...")
    data = []
    for i, row in enumerate(reader):
        try:
            parsed = parse_row(row, log_ix=i + 2)
            data.append(parsed)
        except AssertionError:
            logging.warning(f"R{i+2}: No name")
            continue
    logging.info("Done!")

    logging.info("-" * PRINT_WIDTH)
    logging.info("Fetching placeholder image...")
    logging.info(f"URL: {PLACEHOLDER_IMAGE_URL}")
    fetch_and_write_image(PLACEHOLDER_IMAGE_URL, IMAGE_DIR / "placeholder.jpg")
    logging.info("Done!")

    logging.info("-" * PRINT_WIDTH)
    logging.info("Writing JSON...")
    logging.info(f"File: {OUTPUT_JSON}")
    write_json(data, OUTPUT_JSON)
    logging.info("Done!")
