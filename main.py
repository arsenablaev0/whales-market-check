import requests
import time
import json

BOT_TOKEN = '6532065357:AAEqvipDlENAymDQJAePQmXdh3V_ksNVeNc'
CHAT_ID = 342041283  # узнать можешь здесь : https://t.me/getmyid_bot
token_id='a1a83a52-54ed-44b5-b07e-780ea5c7ea4a'


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        print(f"Failed to send message, status code: {response.status_code}")

def fetch_offers():
    url = "https://api-v2.whales.market/transactions/offers?take=24&page=1&type=sell&token_status=active&full_match=&chain_id=3117&address_ex=&status=open&sort_time=&sort_price=asc&sort_value=&filled=&chains=&category_token=point_market"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data, status code: {response.status_code}")
        return None

def load_previous_offers():
    try:
        with open('offers.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_offers(offers):
    with open('offers.json', 'w') as file:
        json.dump(offers, file, indent=4)

def filter_offer_data(offer):
    return {
        "id": offer["id"],
        "total_amount": offer["total_amount"],
        "priceUsd": offer["offer_price_usd"],
        "valueUsd": offer["offer_collateral_value"],
        "sellsIn": offer["ex_token"]['symbol'],
        "sellsValue": offer["value"],
        "token_symbol": offer["token"]["symbol"]
    }

def process_data(new_data, previous_data):
    new_offers = 0
    offers_by_symbol = {}
    for offer in new_data.get('data', {}).get('list', []):
        filtered_offer = filter_offer_data(offer)
        symbol = filtered_offer['token_symbol']
        if symbol not in offers_by_symbol or offers_by_symbol[symbol]['priceUsd'] > filtered_offer['priceUsd']:
            offers_by_symbol[symbol] = filtered_offer

    # Save new offers to JSON file
    offers_dict = {offer['id']: offer for offer in new_data.get('data', {}).get('list', [])}
    save_offers(offers_dict)

    # Send notifications for the cheapest offers by symbol
    for symbol, offer in offers_by_symbol.items():
        if offer['id'] not in previous_data:
            new_offers+=1
            
            amount = "{:,}".format(offer['total_amount'])
            message = f"✅ Cheapest {symbol} offer: \
                        \nAmount: {amount} \
                        \nPrice USD: {offer['priceUsd']} \
                        \nTotal Price USD: {offer['valueUsd']} \
                        \nFor: {offer['sellsValue']} {offer['sellsIn']}"
            send_telegram_message(message)
            print(f"Notification sent for {symbol} with cheapest price offer.")
            
    return new_offers

def main():
    previous_data = load_previous_offers()
    while True:
        new_data = fetch_offers()
        new_offers_count = process_data(new_data, previous_data)
        # Update previous_data with the latest offers to check for new ones in the next iteration
        previous_data = {offer['id']: offer for offer in new_data.get('data', {}).get('list', [])}
        if new_offers_count > 0:
            print(f"{new_offers_count} new offers found")
        else:
            print("No new offers foud")
        time.sleep(60)  # Adjust as needed

if __name__ == "__main__":
    main()