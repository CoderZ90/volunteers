#!/usr/bin/env python3

import csv
import json
import logging
import requests
import validators
import sys
from collections import defaultdict
from pathlib import Path

# Set logging level
logging.basicConfig(stream=sys.stdout, format="%(message)s", level=logging.INFO)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQpWu2GwKfZF5VQLFGHWuWiPSk-riYszgiKYocCjAJG0vM1HNSZaJ5uAdUCjWoMcbVn1gWPAx2HNj7B/pub?gid=0&single=true&output=csv"

PRINT_WIDTH = 70

OUTPUT_DIR = Path("tmp")
IMAGE_DIR = OUTPUT_DIR / "images"
OUTPUT_JSON = OUTPUT_DIR / "data.json"

ddict = lambda: defaultdict(ddict)


def get_csv(url):
    response = requests.get(url)
    response.raise_for_status()
    lines = response.text.split("\n")
    return csv.DictReader(lines)


def parse_row(row):
    row = {k: v.strip() for k, v in row.items()}

    assert len(row["name"]) > 0

    output = ddict()

    for column in ["name", "bio"]:
        output[column] = row[column]

    if validators.url(row["link"]):
        output["link"] = row["link"].lower()

    for column in ["github", "linkedin", "twitter", "instagram"]:
        if validators.url(row[column]):
            output["socials"][column] = row[column].lower()

    if validators.url(row["image"]):
        slug = f"{row['name'].lower().replace(' ', '-')}-{i}"
        # if write_image(row["image"], IMAGE_DIR / slug):
        #     output["image"] = row["image"]

    return output


def write_image(url, filepath):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        return True
    except:
        return False


def write_json(data, filepath):
    with open(filepath, "w") as f:
        output = sorted(data, key=lambda x: x["name"])
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    reader = get_csv(CSV_URL)

    output = []
    for i, row in enumerate(reader):
        try:
            parsed = parse_row(row)
            output.append(parsed)
        except AssertionError:
            continue

    logging.info("-" * PRINT_WIDTH)
    logging.info("Dumping JSON APIs...")
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(output, OUTPUT_JSON)
