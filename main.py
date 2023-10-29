import pathlib
import time
import threading
import requests
from rich.console import Console

# Read cookie from file
try:
    cookie = pathlib.Path("cookie.txt").read_text()
except (FileNotFoundError, PermissionError):
    print("Error: could not read cookie file")
    exit(1)

# Create session with cookie
session = requests.Session()
session.cookies.update({".ROBLOSECURITY": cookie})

# Create console object for printing
console = Console(highlight=False)

# Print colored text to console
def cprint(color: str, content: str) -> None:
    console.print(f"[ [bold {color}]>[/] ] {content}")

# Print banner in separate thread
def print_banner():
    cprint("green", "Made by Gian!#000! | pdfz")

threading.Thread(target=print_banner, daemon=True).start()

# Fetch items from Roblox API
def fetch_items(url: str) -> dict:
    result = {}
    cursor = ""

    while cursor is not None:
        req = session.get(url + f"&cursor={cursor}")
        res = None

        try:
            res = req.json()
        except ValueError:
            cprint("red", f"Invalid JSON response: {req.text}")
            continue

        if req.status_code == 429:
            cprint("red", "Rate limited. Waiting 20 seconds")
            time.sleep(20)
            continue

        for item in res.get("data", []):
            item_name = item.get("name")
            if item.get("creatorTargetId") != 1:
                product_id = item.get("productId")
                if product_id is not None:
                    result[item_name] = product_id
                    cprint("blue", f"Found {item_name}")

        cursor = res.get("nextPageCursor")

    return result

# Check if user owns a product
def check_ownership(product_id: int) -> bool:
    req = session.get(f"https://economy.roblox.com/v1/products/{product_id}/ownership")

    if req.status_code == 200:
        return True
    elif req.status_code == 404:
        return False
    else:
        raise Exception(f"Unexpected response code: {req.status_code}")

# Save bought items to file
def save_bought_items(product_id: int) -> None:
    try:
        with open("bought.txt", "a") as f:
            f.write(f"{product_id}\n")
    except (FileNotFoundError, PermissionError):
        cprint("red", "Error: could not write to bought.txt")
        return

    # Skip invalid lines
    with open("bought.txt", "r") as f:
        bought_items = set()
        for line in f:
            line = line.strip()
            if line.isdigit():
                bought_items.add(int(line))

    with open("bought.txt", "w") as f:
        for item in bought_items:
            f.write(f"{item}\n")

# Purchase a product
# Purchase a product
def purchase(product_id: int) -> None:
    with open("bought.txt", "r") as f:
        bought_items = set()
        for line in f:
            line = line.strip()
            if line.isdigit():
                bought_items.add(int(line))

    if product_id in bought_items:
        cprint("yellow", f"Item {product_id} has already been bought")
        return

    save_bought_items(product_id)

    # Login to Roblox
    req = session.post("https://auth.roblox.com/v2/login")
    csrf_token = req.headers["x-csrf-token"]

    while True:
        # Purchase product
        req = session.post(
            f"https://economy.roblox.com/v1/purchases/products/{product_id}",
            json={"expectedCurrency": 1, "expectedPrice": 0, "expectedSellerId": 1},
            headers={"X-CSRF-TOKEN": csrf_token},
        )

        if req.status_code == 429:
            retry_after = int(req.headers.get("retry-after", "60"))
            cprint("red", f"Rate limited. Waiting {retry_after} seconds")
            time.sleep(retry_after)
            continue

        res = req.json()

        if "reason" in res and res.get("reason") == "AlreadyOwned":
            cprint("yellow", f"Item {product_id} is already owned")
            return

        cprint("green", f"Successfully purchased item {product_id}")
        return

    save_bought_items(product_id)

    # Login to Roblox
    req = session.post("https://auth.roblox.com/v2/login")
    csrf_token = req.headers["x-csrf-token"]

    while True:
        # Purchase product
        req = session.post(
            f"https://economy.roblox.com/v1/purchases/products/{product_id}",
            json={"expectedCurrency": 1, "expectedPrice": 0, "expectedSellerId": 1},
            headers={"X-CSRF-TOKEN": csrf_token},
        )

        if req.status_code == 429:
            cprint("red", "Rate limited. Waiting 60 seconds")
            time.sleep(60)
            continue

        res = req.json()

        if "reason" in res and res.get("reason") == "AlreadyOwned":
            cprint("yellow", f"Item {product_id} is already owned")
            return

        cprint("green", f"Successfully purchased item {product_id}")
        return

# Main function
def main() -> None:
    "Purchases all free items from the Roblox Marketplace, including UGC items, checking"

    # Purchase free items
    free_items = fetch_items("https://catalog.roblox.com/v1/search/items/details?category=All&limit=30&maxPrice=1")
    for product_id in free_items.values():
        if not check_ownership(product_id):
            purchase(product_id)

if __name__ == "__main__":
    main()
