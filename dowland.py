import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/"
OUT = "mars2020_meda"

# CINT-70 selected mission periods
SOL_FOLDERS = [
    "sol_0000_0089",
    "sol_0900_1019",
    "sol_1620_1739"
]

# Main files
FILES = [
    "bundle.xml",
    "readme.txt",

    "data_calibrated_env/collection_meda_data_calibrated_env.xml",
    "data_calibrated_env/collection_meda_data_calibrated_env_inventory.csv",

    "data_derived_env/collection_meda_data_derived_env.xml",
    "data_derived_env/collection_meda_data_derived_env_inventory.csv",
]


def download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        print("Exists:", path)
        return

    print("Downloading:", url)

    r = requests.get(url, timeout=120)

    if r.status_code == 200:
        with open(path, "wb") as f:
            f.write(r.content)
        print("Saved:", path)
    else:
        print("FAILED:", url)


def download_directory(folder):

    url = urljoin(BASE, folder)

    print("\nScanning:", url)

    r = requests.get(url, timeout=120)

    soup = BeautifulSoup(r.text, "html.parser")

    for link in soup.find_all("a"):

        name = link.get("href")

        if not name:
            continue

        if name.endswith((".xml", ".tab", ".csv")):

            file_url = urljoin(url, name)

            save_path = os.path.join(
                OUT,
                folder,
                name
            )

            download(file_url, save_path)


# Download metadata
for f in FILES:
    download(
        urljoin(BASE, f),
        os.path.join(OUT, f)
    )


# Download calibrated environment data
for sol in SOL_FOLDERS:

    folder = (
        "data_calibrated_env/"
        + sol
        + "/"
    )

    download_directory(folder)


# Download derived environment data
for sol in SOL_FOLDERS:

    folder = (
        "data_derived_env/"
        + sol
        + "/"
    )

    download_directory(folder)


print("\n==============================")
print("MEDA CINT-70 DOWNLOAD COMPLETE")
print("==============================")