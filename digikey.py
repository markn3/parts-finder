import requests

class DigiKeyAPI:
    def __init__(self, client_id, client_secret, currency, language, localsite):
        self.client_id = client_id
        self.client_secret = client_secret
        self.localSite = localsite
        self.localCurrency = currency
        self._get_access_token()

    def _get_access_token(self):
        url = "https://api.digikey.com/v1/oauth2/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            token_info = response.json()
            self.token_expirationIn = token_info['expires_in']
            self.tokenValue = token_info['access_token']
            print("Access token retrieved successfully.")
        else:
            print(f"Error: {response.status_code}, {response.text}")
            self.token_expirationIn = 0
            self.tokenValue = ""

    def search_partNumber(self, part_number, quantity):
        url = f"https://api.digikey.com/products/v4/search/{part_number}/productdetails"
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + self.tokenValue,
            "X-DIGIKEY-Client-Id": self.client_id,
            "X-DIGIKEY-Locale-Site": self.localSite,
            "X-DIGIKEY-Locale-Currency": self.localCurrency,
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                product_details = response.json()
            else:
                print(f"Error: {response.status_code}, {response.text}")
                return None

            # Return the parsed component data
            return self.parseComponentResponse(response.json(), part_number)

        except requests.exceptions.RequestException as e:
            print(f"Error during the request: {e}")
            return None

    def parseComponentResponse(self, component_result, part_number):
        components = []

        if (component_result
                and "Product" in component_result
                and isinstance(component_result["Product"], dict)):
            component_data = self.extract_component_data(component_result["Product"], part_number)
            if component_data:
                components.append(component_data)
                return components

        return components

    def extract_component_data(self, component_json, part_number):
        try:
            # Verify that the ManufacturerProductNumber matches the part_number
            if (component_json.get("ManufacturerProductNumber") != part_number):
                return None

            availability = component_json.get("QuantityAvailable", "0")
            manufacturer = component_json["Manufacturer"]["Name"]
            lifeCycleStatus = component_json["ProductStatus"]["Status"]
            prices = {}
            try:
                standard_pricing = component_json["ProductVariations"][1]['StandardPricing']
            except IndexError:
                standard_pricing = component_json["ProductVariations"][0]['StandardPricing']

            for price in standard_pricing:
                break_quantity = price.get("BreakQuantity", 0)
                price_value = price.get("UnitPrice", "0")
                prices[break_quantity] = price_value

            return {
                "availability": availability,
                "manufacturer": manufacturer,
                "prices": prices,
                "currency": self.localCurrency,
                "lifeCycleStatus": lifeCycleStatus,
            }
        except (ValueError, KeyError, TypeError) as e:
            print(f"Error extracting component data: {e}")
            return None

    def get_price_for_quantity(self, component, quantity):
        prices = component.get("prices", {})
        sorted_quantities = sorted(prices.keys(), key=lambda x: int(x))

        applicable_price = None
        optimal_price_quantity = None
        recommended_units = quantity

        for q in sorted_quantities:
            if quantity >= int(q):
                applicable_price = prices[q]
            elif applicable_price is None:
                applicable_price = prices[q]
                recommended_units = int(q)
                break

        if applicable_price is None:
            return {
                "unit_price": None,
                "total_price": None,
                "is_optimal": False,
                "recommended_units": None,
                "recommended_price": None,
                "message": "No price available for the given quantity."
            }

        unit_price = float(applicable_price)
        total_price = unit_price * recommended_units

        # Check for an optimal price break for larger quantities
        is_optimal = True
        recommended_price = unit_price
        for q in sorted_quantities:
            if int(q) > quantity:
                future_unit_price = float(prices[q])
                future_total_price = future_unit_price * int(q)
                if future_total_price < total_price:
                    is_optimal = False
                    optimal_price_quantity = int(q)
                    recommended_units = int(q)
                    recommended_price = future_unit_price
                    total_price = future_total_price
                    break

        return {
            "unit_price": unit_price,
            "total_price": total_price,
            "is_optimal": is_optimal,
            "recommended_units": recommended_units,
            "recommended_price": recommended_price,
            "message": "Optimal price found" if is_optimal else f"Better price available for {optimal_price_quantity} units."
        }


if __name__ == "__main__":
    # Update these values with your actual credentials and settings
    CLIENT_ID = "Qss9g4pvT1XF9G3VIpwGS9cq3AeEEWum"
    CLIENT_SECRET = "O04s4GO8xNAPsFoU"
    CURRENCY = "USD"          # e.g., USD
    LANGUAGE = "en"           # not actively used in the code, but available if needed
    LOCAL_SITE = "US"         # e.g., US for United States

    # Instantiate the DigiKeyAPI class
    digikey_api = DigiKeyAPI(CLIENT_ID, CLIENT_SECRET, CURRENCY, LANGUAGE, LOCAL_SITE)

    # Prompt user for input
    part_number = input("Enter a RealTek part number (e.g., RTL1234): ").strip()
    if not part_number:
        part_number = "RTL1234"  # default test value

    quantity_input = input("Enter quantity (default is 1): ").strip()
    try:
        quantity = int(quantity_input) if quantity_input else 1
    except ValueError:
        print("Invalid quantity input, defaulting to 1.")
        quantity = 1

    # Search for the part number and display the results
    print(f"\nSearching for part: {part_number} with quantity: {quantity} ...\n")
    search_results = digikey_api.search_partNumber(part_number, quantity)
    
    if search_results:
        print("Search Results:")
        for component in search_results:
            print(component)
        
        # If a component is found, try to compute the price for the given quantity
        if search_results:
            pricing_info = digikey_api.get_price_for_quantity(search_results[0], quantity)
            print("\nPricing Information:")
            print(pricing_info)
    else:
        print("No data returned from Digi-Key for the specified part number.")
