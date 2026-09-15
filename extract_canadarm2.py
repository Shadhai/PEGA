"""
Extract Canadarm2 specifications from CSA website.
"""
import requests
from bs4 import BeautifulSoup
import json
import re

URL = "https://www.asc-csa.gc.ca/eng/iss/canadarm2/"

def extract_specs():
    print(f"Fetching {URL}...")
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, "lxml")

    # Find tables or text containing joint info
    # We'll search for patterns like "shoulder" or "joint"
    text = soup.get_text("\n", strip=True)

    # Save text for manual inspection
    with open("data/extracted/canadarm2_page.txt", "w", encoding="utf-8") as f:
        f.write(text)

    # Try to find specific specs using regex
    specs = {}

    # Degrees of freedom
    dof_match = re.search(r'(\d+)\s*degrees of freedom', text, re.I)
    if dof_match:
        specs["degrees_of_freedom"] = int(dof_match.group(1))

    # Length
    length_match = re.search(r'(\d+\.?\d*)\s*m', text)
    if length_match:
        specs["length_m"] = float(length_match.group(1))

    # Payload capacity
    payload_match = re.search(r'(\d+(?:,\d{3})*)\s*kg', text)
    if payload_match:
        specs["payload_capacity_kg"] = int(payload_match.group(1).replace(",", ""))

    print("Extracted so far:", specs)
    print("Full page text saved to data/extracted/canadarm2_page.txt")
    print("Please inspect that file for joint-specific values (like ranges and velocities).")

if __name__ == "__main__":
    extract_specs()