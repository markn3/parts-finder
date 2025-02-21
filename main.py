from bs4 import BeautifulSoup
import requests

# Example configuration for the parts and supplier endpoints.
PARTS = [
    {"part_number": "RTL8153B", "description": "RealTek Chip A"},
    {"part_number": "RTL8153-vc", "description": "RealTek Chip B"},
    {"part_number": "RTL8153e", "description": "RealTek Chip C"}
]

SUPPLIERS = [
    {
        "name": "DigiKey",
        "type": "api",
        "endpoint": "https://api.digikey.com/products/v4/search/keyword",
        "params": {"apikey": "YOUR_DIGIKEY_API_KEY"}  # example parameter
    },
    {
        "name": "SupplierScrapeSite",
        "type": "scrape",
        "endpoint": "https://www.example.com/search?q="
    }
]


def fetch_from_api(part, supplier):
    """Fetch part info using an API call."""
    params = supplier.get("params", {}).copy()
    params["q"] = part["part_number"]
    try:
        response = requests.get(supplier["endpoint"], params=params)
        response.raise_for_status()
        data = response.json()
        # Extract relevant fields – customize based on API response structure
        result = {
            "price": data.get("price", "N/A"),
            "availability": data.get("availability", "N/A"),
            "url": data.get("productUrl", "")
        }
        return result
    except Exception as e:
        print(f"Error fetching from {supplier['name']}: {e}")
        return None


def fetch_from_scrape(part, supplier):
    """Fetch part info by scraping a website."""
    url = supplier["endpoint"] + part["part_number"]
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Customize selectors based on the website's HTML structure
        price_elem = soup.find("span", class_="price")
        avail_elem = soup.find("div", class_="availability")
        result = {
            "price": price_elem.text.strip() if price_elem else "N/A",
            "availability": avail_elem.text.strip() if avail_elem else "N/A",
            "url": url
        }
        return result
    except Exception as e:
        print(f"Error scraping {supplier['name']}: {e}")
        return None

def aggregate_data():
    aggregated_results = {}
    for part in PARTS:
        aggregated_results[part["part_number"]] = {}
        for supplier in SUPPLIERS:
            if supplier["type"] == "api":
                data = fetch_from_api(part, supplier)
            elif supplier["type"] == "scrape":
                data = fetch_from_scrape(part, supplier)
            else:
                data = None
            aggregated_results[part["part_number"]][supplier["name"]] = data
    return aggregated_results

if __name__ == "__main__":
    results = aggregate_data()
    for part_number, supplier_data in results.items():
        print(f"Results for {part_number}:")
        for supplier_name, data in supplier_data.items():
            print(f"  {supplier_name}: {data}")