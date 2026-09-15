# # save as: download_meda_thermal.py
# # Run: python download_meda_thermal.py

# import os
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin

# def download_sol_data(base_url, sol_range, local_base):
#     """Download only TIRS, ATS, RDS files from a sol range"""
    
#     url = f"{base_url}{sol_range}/"
#     local_dir = os.path.join(local_base, sol_range)
#     os.makedirs(local_dir, exist_ok=True)
    
#     print(f"\nScanning: {url}")
#     response = requests.get(url)
#     soup = BeautifulSoup(response.text, 'html.parser')
    
#     for link in soup.find_all('a'):
#         href = link.get('href')
#         if href in ['.', '..', '/', '../', 'Parent Directory']:
#             continue
        
#         if href.endswith('/'):
#             # Subdirectory like sol_0009/
#             sol_url = urljoin(url, href)
#             sol_dir = os.path.join(local_dir, href.rstrip('/'))
#             os.makedirs(sol_dir, exist_ok=True)
            
#             print(f"  Scanning: {href}")
#             sol_response = requests.get(sol_url)
#             sol_soup = BeautifulSoup(sol_response.text, 'html.parser')
            
#             for file_link in sol_soup.find_all('a'):
#                 filename = file_link.get('href')
#                 if filename in ['.', '..', '/', '../']:
#                     continue
                
#                 # Only download TIRS, ATS, RDS (what we need for thermal data)
#                 if any(sensor in filename.upper() for sensor in ['TIRS', 'ATS', 'RDS']):
#                     if filename.endswith('.CSV'):
#                         file_url = urljoin(sol_url, filename)
#                         filepath = os.path.join(sol_dir, filename)
                        
#                         print(f"    Downloading: {filename}")
#                         try:
#                             r = requests.get(file_url, timeout=30)
#                             with open(filepath, 'wb') as f:
#                                 f.write(r.content)
#                         except Exception as e:
#                             print(f"    Failed: {e}")

# # Download only what CINT-70 needs
# base = "https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/data_calibrated_env/"

# sol_ranges = [
#     "sol_0000_0089",
#     "sol_0900_1019", 
#     "sol_1620_1739"
# ]

# for sol_range in sol_ranges:
#     download_sol_data(base, sol_range, "data/raw_sources/mars2020_meda/data_calibrated_env")

# print("\n✅ Thermal data downloaded!")
"""
CINT-70: Download MEDA Derived Environment Data
Completes the Mars 2020 MEDA dataset
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import time

def download_file(url, filepath):
    """Download a single file with retry"""
    try:
        r = requests.get(url, timeout=30)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"    Failed: {e}")
        return False

def download_sol_range(base_url, sol_range, max_sols=10):
    """Download first N sols from a range"""
    sol_url = urljoin(base_url, sol_range + "/")
    local_base = f"data/raw_sources/mars2020_meda/data_derived_env/{sol_range}"
    
    print(f"\nScanning: {sol_url}")
    r = requests.get(sol_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    sols = [a.get('href') for a in soup.find_all('a') 
            if a.get('href', '').startswith('sol_')]
    
    count = 0
    for sol in sols[:max_sols]:
        sol_name = sol.rstrip('/')
        sol_dir_url = urljoin(sol_url, sol)
        local_dir = os.path.join(local_base, sol_name)
        
        print(f"  Sol: {sol_name}")
        
        try:
            r2 = requests.get(sol_dir_url, timeout=30)
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            
            for link in soup2.find_all('a'):
                fname = link.get('href')
                if fname.endswith('.CSV') or fname.endswith('.xml'):
                    file_url = urljoin(sol_dir_url, fname)
                    filepath = os.path.join(local_dir, fname)
                    
                    if not os.path.exists(filepath):
                        if download_file(file_url, filepath):
                            count += 1
                        time.sleep(0.5)  # Be nice to NASA servers
        except Exception as e:
            print(f"    Error: {e}")
    
    return count

if __name__ == "__main__":
    print("=" * 60)
    print("CINT-70: MEDA Derived Data Downloader")
    print("=" * 60)
    
    base = "https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/data_derived_env/"
    
    # Step 1: Download metadata files
    print("\n[1/3] Downloading metadata...")
    for meta_file in [
        "collection_meda_data_derived_env.xml",
        "collection_meda_data_derived_env_inventory.csv"
    ]:
        url = urljoin(base, meta_file)
        filepath = f"data/raw_sources/mars2020_meda/data_derived_env/{meta_file}"
        if download_file(url, filepath):
            print(f"  ✅ {meta_file}")
    
    # Step 2: Download early mission data
    print("\n[2/3] Downloading sol_0000_0089 (early mission)...")
    count1 = download_sol_range(base, "sol_0000_0089", max_sols=8)
    
    # Step 3: Download later mission data
    print("\n[3/3] Downloading sol_1620_1739 (later mission)...")
    count2 = download_sol_range(base, "sol_1620_1739", max_sols=8)
    
    print(f"\n{'='*60}")
    print(f"✅ DERIVED DATA DOWNLOAD COMPLETE")
    print(f"   Files downloaded: {count1 + count2}")
    print(f"   Location: data/raw_sources/mars2020_meda/data_derived_env/")
    print(f"{'='*60}")