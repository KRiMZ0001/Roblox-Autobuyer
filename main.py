import pathlib
import time
import requests
from rich.console import Console

cookie = pathlib.Path("cookie.txt").read_text()

session = requests.Session()
session.cookies.update({".ROBLOSECURITY": cookie})

console = Console(highlight=False)


def cprint(color: str, content: str) -> None:
  console.print(f"[ [bold {color}]>[/] ] {content}")


def fetch_items() -> None:
  """Fetches a list of all free items on the Roblox Marketplace, including UGC items.

  Returns:
    A dictionary of free items, where the keys are the item names and the values are the product IDs.
  """

  result = {}
  cursor = ""

  while cursor is not None:
    req = session.get(
        f"https://catalog.roblox.com/v1/search/items/details?category=All&limit=30&maxPrice=0&cursor={cursor}"
    )
    res = req.json()

    if req.status_code == 429:
      cprint("red", "Rate limited. Waiting 20 seconds")
      time.sleep(20)
      continue

    for item in res.get("data", []):
      item_name = item.get("name")
      if item.get("creatorTargetId") != 1:
        result[item_name] = item.get("productId")
        cprint("blue", f"Found {item_name}")

    cursor = res.get("nextPageCursor")

  return result


def check_ownership(product_id: int) -> bool:
  """Checks if the current user owns a free item.

  Args:
    product_id: The product ID of the free item.

  Returns:
    True if the current user owns the item, False otherwise.
  """

  req = session.get(f"https://economy.roblox.com/v1/products/{product_id}/ownership")

  if req.status_code == 200:
    return True
  elif req.status_code == 404:
    return False
  else:
    raise Exception(f"Unexpected response code: {req.status_code}")


def save_bought_items(product_id: int) -> None:
  """Saves the product ID of a bought item to a file.

  Args:
    product_id: The product ID of the bought item.
  """

  with open("bought.txt", "a") as f:
    f.write(f"{product_id}\n")


def purchase(product_id: int) -> None:
  """Purchases a free item from the Roblox Marketplace and saves the product ID to a file.

  Args:
    product_id: The product ID of the free item to purchase.
  """

  # Check if the item has already been bought
  with open("bought.txt", "r") as f:
    bought_items = set(int(line.strip()) for line in f)

  if product_id in bought_items:
    cprint("yellow", f"Item {product_id} has already been bought")
    return

  save_bought_items(product_id)

  req = session.post(
      "https://auth.roblox.com/v2/login"
  )
  csrf_token = req.headers["x-csrf-token"]

  while True:
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


def main() -> None:
  "Purchases all free items from the Roblox Marketplace, including UGC items, checking"

free_items = fetch_items()

for product_id in free_items.values():
  if not check_ownership(product_id):
    purchase(product_id)
