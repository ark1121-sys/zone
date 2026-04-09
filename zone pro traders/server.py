import http.server
import socketserver
import requests
import sys
import re
import os
import json
import ssl
import urllib.parse
from bs4 import BeautifulSoup

PORT = 8000
try:
    PORT = int(os.environ.get('PORT', PORT))
except:
    pass
if len(sys.argv) > 1:
    try:
        PORT = int(sys.argv[1])
    except:
        pass
CHARTINK_BASE = "https://chartink.com"
FIREBASE_DB_URL = "https://zone-pro-trader-a7870-default-rtdb.firebaseio.com"
RUNTIME_STORE = {"trades": {}}
FIREBASE_AUTH = os.environ.get('FIREBASE_AUTH')

# Heatmap Configuration
HEATMAP_DOMAIN_MAP = {
    "HDFCBANK": "hdfcbank.com", "ICICIBANK": "icicibank.com", "SBIN": "sbi.co.in",
    "AXISBANK": "axisbank.com", "KOTAKBANK": "kotak.com", "BAJFINANCE": "bajajfinserv.in",
    "BAJAJFINSV": "bajajfinserv.in", "INDUSINDBK": "indusind.com", "HDFCLIFE": "hdfclife.com",
    "TCS": "tcs.com", "INFY": "infosys.com", "WIPRO": "wipro.com", "HCLTECH": "hcltech.com",
    "TECHM": "techmahindra.com", "RELIANCE": "ril.com", "HINDUNILVR": "hul.co.in",
    "ITC": "itcportal.com", "NESTLEIND": "nestle.in", "MARUTI": "marutisuzuki.com", "TATAMOTORS": "tatamotors.com", "TITAN": "titancompany.in",
    "M&M": "mahindra.com", "SUNPHARMA": "sunpharma.com", "LT": "larsentoubro.com",
    "NTPC": "ntpc.co.in", "POWERGRID": "powergrid.in", "BHARTIARTL": "airtel.in",
    "ULTRACEMCO": "ultratechcement.com", "JSWSTEEL": "jsw.in", "TATASTEEL": "tatasteel.com",
    "ASIANPAINT": "asianpaints.com", "ADANIENT": "adani.com", "ADANIPORTS": "adaniports.com",
    "COALINDIA": "coalindia.in", "ONGC": "ongcindia.com", "GRASIM": "grasim.com",
    "DRREDDY": "drreddys.com", "CIPLA": "cipla.com", "APOLLOHOSP": "apollohospitals.com",
    "TATACONSUM": "tataconsumerproducts.com", "EICHERMOT": "eichermotors.com", "BAJAJ-AUTO": "bajajauto.com",
    "HDFCLIFE": "hdfclife.com", "BPCL": "bpcl.in", "HINDALCO": "hindalco.com",
    "SHRIRAMFIN": "shriramfinance.in"
}

HEATMAP_SECTOR_MAP = {
    "HDFCBANK": "Finance", "ICICIBANK": "Finance", "SBIN": "Finance", "AXISBANK": "Finance",
    "KOTAKBANK": "Finance", "BAJFINANCE": "Finance", "BAJAJFINSV": "Finance", "INDUSINDBK": "Finance",
    "TCS": "Technology Services", "INFY": "Technology Services", "WIPRO": "Technology Services",
    "HCLTECH": "Technology Services", "TECHM": "Technology Services", "RELIANCE": "Energy Minerals",
    "MARUTI": "Consumer Durables", "TATAMOTORS": "Consumer Durables", "M&M": "Consumer Durables",
    "TITAN": "Consumer Durables", "HINDUNILVR": "Consumer Non-Durables", "ITC": "Consumer Non-Durables",
    "NESTLEIND": "Consumer Non-Durables", "SUNPHARMA": "Health Technology", "LT": "Industrial Services",
    "NTPC": "Utilities", "POWERGRID": "Utilities", "BHARTIARTL": "Communications",
    "ULTRACEMCO": "Non Energy Minerals", "JSWSTEEL": "Non Energy Minerals", "TATASTEEL": "Non Energy Minerals",
    "ASIANPAINT": "Process Industries", "ADANIENT": "Energy Minerals", "ADANIPORTS": "Industrial Services",
    "COALINDIA": "Energy Minerals", "ONGC": "Energy Minerals", "GRASIM": "Process Industries",
    "DRREDDY": "Health Technology", "CIPLA": "Health Technology", "APOLLOHOSP": "Health Technology",
    "TATACONSUM": "Consumer Non-Durables", "EICHERMOT": "Consumer Durables", "BAJAJ-AUTO": "Consumer Durables",
    "HDFCLIFE": "Finance", "BPCL": "Energy Minerals", "HINDALCO": "Non Energy Minerals",
    "SHRIRAMFIN": "Finance"
}

HEATMAP_SIZE_MAP = {
    "HDFCBANK": 10, "ICICIBANK": 7, "SBIN": 6, "AXISBANK": 4, "KOTAKBANK": 4,
    "BAJFINANCE": 4, "BAJAJFINSV": 4, "INDUSINDBK": 3, "TCS": 8, "INFY": 7,
    "HCLTECH": 5, "WIPRO": 4, "TECHM": 3, "RELIANCE": 9, "HINDUNILVR": 6,
    "ITC": 5, "NESTLEIND": 4, "MARUTI": 4, "TATAMOTORS": 4, "M&M": 3,
    "TITAN": 4, "LT": 6, "NTPC": 3, "POWERGRID": 3, "BHARTIARTL": 5,
    "ULTRACEMCO": 4, "JSWSTEEL": 3, "TATASTEEL": 4, "SUNPHARMA": 4, "ASIANPAINT": 3,
    "ADANIENT": 3, "ADANIPORTS": 3, "COALINDIA": 3, "ONGC": 3, "GRASIM": 3,
    "DRREDDY": 3, "CIPLA": 3, "APOLLOHOSP": 3, "TATACONSUM": 3, "EICHERMOT": 3,
    "BAJAJ-AUTO": 3, "HDFCLIFE": 3, "BPCL": 3, "HINDALCO": 3, "SHRIRAMFIN": 3
}

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # First, let the base class do its thing
        original_path = super().translate_path(path)
        if os.path.exists(original_path) and os.path.isfile(original_path):
            return original_path

        # If not found, try our custom locations
        parsed_url = urllib.parse.urlparse(path)
        decoded_path = urllib.parse.unquote(parsed_url.path).lstrip('/')
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        search_dirs = [
            os.path.join(current_dir, 'assets'),
            os.path.join(current_dir, 'assets/images'),
            os.path.join(current_dir, 'assets/css'),
            os.path.join(current_dir, 'assets/js'),
            os.path.join(current_dir, 'pages')
        ]
        
        for d in search_dirs:
            p = os.path.join(d, decoded_path)
            if os.path.exists(p) and os.path.isfile(p):
                return p
        
        return original_path

    def do_GET(self):
        # Parse path and query
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # 1. API routes
        if path.startswith('/api/'):
            if path == '/api/pdh-data': self.handle_pdh_data()
            elif path == '/api/swing-data': self.handle_swing_data()
            elif path == '/api/ipo-data': self.handle_ipo_data()
            elif path == '/api/pdl-data': self.handle_pdl_data()
            elif path == '/api/heatmap': self.handle_heatmap()
            elif path.startswith('/api/db/ping'): self.handle_db_ping()
            elif path.startswith('/api/trades'): self.handle_trades_list()
            else: self.send_error(404, "API Not Found")
            return

        # 2. Chartink proxy routes
        chartink_paths = [
            '/screener', '/build', '/uploads', '/cdn-cgi', '/imgs', '/css', '/js', 
            '/fonts', '/images', '/assets', '/favicon', '/ajax', '/api-data',
            '/stocks', '/process', '/explore', '/backtest', '/charts', '/notices'
        ]
        
        # Check if it's a local file first (to avoid proxying local assets that might match chartink_paths)
        local_path = self.translate_path(self.path)
        if os.path.exists(local_path) and os.path.isfile(local_path):
            if self.path == '/':
                self.path = '/index.html'
            super().do_GET()
            return

        if any(self.path.startswith(prefix) for prefix in chartink_paths):
            if self.path.startswith('/screener/') and not self.headers.get('X-Requested-With'):
                self.handle_chartink_page(self.path)
            else:
                self.handle_proxy_request('GET')
            return

        # Fallback to standard handler (which will use translate_path again)
        if self.path == '/':
            self.path = '/index.html'
        super().do_GET()

    def do_POST(self):
        # Proxy all POST requests that match Chartink paths
        proxy_prefixes = [
            '/screener', '/build', '/uploads', '/cdn-cgi', '/imgs', '/css', '/js', 
            '/fonts', '/images', '/assets', '/favicon', '/ajax', '/api-data',
            '/stocks', '/process', '/explore', '/backtest', '/charts'
        ]
        if any(self.path.startswith(prefix) for prefix in proxy_prefixes):
            self.handle_proxy_request('POST')
        else:
            if self.path.startswith('/api/trades'):
                self.handle_trades_add()
            else:
                self.send_error(404, "Not Found")

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _firebase_url(self, path):
        path = path.strip('/')
        base = f"{FIREBASE_DB_URL}/{path}.json"
        # Prefer per-request token from header, then query, then env
        token = self.headers.get('X-FIREBASE-ID-TOKEN')
        if not token:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            token = (qs.get('idToken') or [None])[0]
        if not token:
            token = FIREBASE_AUTH
        if token:
            return f"{base}?auth={token}"
        return base

    def _get_uid(self):
        uid = self.headers.get('X-UID')
        if not uid:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            uid = (qs.get('uid') or [None])[0]
        return uid

    def handle_db_ping(self):
        try:
            url = self._firebase_url('')
            r = requests.get(url, timeout=8)
            ok = (r.status_code == 200)
            self._send_json(200, {"ok": ok, "status": r.status_code})
        except Exception as e:
            self._send_json(500, {"ok": False, "error": str(e)})

    def handle_trades_list(self):
        try:
            uid = self._get_uid()
            if not uid:
                self._send_json(400, {"error": "uid required"})
                return
            url = self._firebase_url(f"trades/{uid}")
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json() or {}
            else:
                # Fallback to in-memory storage
                data = RUNTIME_STORE["trades"].get(uid, {})
            items = []
            for k, v in data.items():
                if isinstance(v, dict):
                    v["id"] = k
                    items.append(v)
            self._send_json(200, {"items": items})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def handle_trades_add(self):
        try:
            uid = self._get_uid()
            if not uid:
                self._send_json(400, {"error": "uid required"})
                return
            content_length = int(self.headers.get('Content-Length', 0))
            body = {}
            if content_length > 0:
                raw = self.rfile.read(content_length)
                try:
                    body = json.loads(raw.decode('utf-8'))
                except:
                    body = {}
            body.setdefault("createdAt", int(__import__('time').time() * 1000))
            url = self._firebase_url(f"trades/{uid}")
            r = requests.post(url, json=body, timeout=10)
            if r.status_code in (200, 201):
                res = r.json() or {}
                self._send_json(200, {"id": res.get("name"), "ok": True})
            else:
                uid_bucket = RUNTIME_STORE["trades"].setdefault(uid, {})
                new_id = "local_" + str(len(uid_bucket) + 1)
                uid_bucket[new_id] = dict(body)
                self._send_json(200, {"id": new_id, "ok": True, "storage": "runtime"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def handle_heatmap(self):
        NSE_URL = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/market-data/live-equity-market",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        try:
            # We need to hit the main page first to get cookies
            session = requests.Session()
            session.get("https://www.nseindia.com/", headers=headers, timeout=10)
            
            r = session.get(NSE_URL, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json().get('data', [])
                formatted = []
                for stock in data:
                    symbol = stock.get('symbol')
                    try:
                        p_change = stock.get('pChange', 0)
                        # Handle cases where pChange might be a string like "-"
                        if isinstance(p_change, str):
                            p_change = p_change.replace(',', '')
                            if p_change.strip() == '-':
                                p_change = 0
                        
                        change_val = float(p_change)
                    except (ValueError, TypeError):
                        change_val = 0

                    formatted.append({
                        "symbol": symbol,
                        "change": change_val,
                        "sector": HEATMAP_SECTOR_MAP.get(symbol, "Others"),
                        "weight": HEATMAP_SIZE_MAP.get(symbol, 1),
                        "domain": HEATMAP_DOMAIN_MAP.get(symbol)
                    })
                # Sort by weight descending
                formatted.sort(key=lambda x: x['weight'], reverse=True)
                self._send_json(200, formatted)
            else:
                print(f"NSE API Error: {r.status_code} for {NSE_URL}")
                self._send_json(r.status_code, {"error": f"NSE API returned {r.status_code}"})
        except Exception as e:
            print(f"Heatmap Exception: {str(e)}")
            self._send_json(500, {"error": str(e)})

    def handle_ipo_data(self):
        url = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                self.send_error(500, f"IPO Watch fetch failed: {response.status_code}")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            
            data = []
            
            # Process Table 0 (Mainboard IPOs usually) and Table 1 (SME IPOs usually)
            # We will combine them or label them
            for i, table in enumerate(tables):
                if i > 1: break # Limit to first 2 tables (usually active ones)
                
                rows = table.find_all('tr')
                if not rows: continue
                
                # Extract headers
                headers_list = [th.get_text(strip=True) for th in rows[0].find_all(['th', 'td'])]
                
                # Extract rows
                table_rows = []
                for row in rows[1:]:
                    cols = [td.get_text(strip=True) for td in row.find_all('td')]
                    if cols:
                        table_rows.append(cols)
                
                data.append({
                    "title": "Mainboard IPOs" if i == 0 else "SME IPOs",
                    "headers": headers_list,
                    "rows": table_rows
                })

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))

        except Exception as e:
            self.send_error(500, f"Error processing IPO data: {str(e)}")

    def handle_pdl_data(self):
        url = "https://chartink.com/screener/pdl-breakdown-stocks"
        try:
            session = requests.Session()
            
            # 1. Fetch main page
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://chartink.com/"
            }
            response = session.get(url, headers=headers)
            
            if response.status_code != 200:
                self.send_error(500, f"Chartink fetch failed: {response.status_code}")
                return

            # 2. Extract CSRF Token
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if not csrf_meta:
                self.send_error(500, "Could not find CSRF token")
                return
            csrf_token = csrf_meta['content']

            # 3. Extract scan_json -> scan_clause
            scan_json_match = re.search(r':scan-json=\'([^\']+)\'', response.text)
            if not scan_json_match:
                 scan_json_match = re.search(r':scan-json="([^"]+)"', response.text)
            
            if not scan_json_match:
                self.send_error(500, "Could not extract scan_json")
                return

            import html
            scan_json_str = html.unescape(scan_json_match.group(1))
            scan_data = json.loads(scan_json_str)
            
            # Use atlas_query or scan_clause string
            scan_clause = scan_data.get('scan_clause')
            if not scan_clause:
                scan_clause = scan_data.get('atlas_query')
            
            if not scan_clause:
                 self.send_error(500, "Could not find scan_clause or atlas_query")
                 return

            # 4. POST to process
            post_url = "https://chartink.com/screener/process"
            post_headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-CSRF-TOKEN": csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://chartink.com",
                "Referer": url,
            }
            
            post_data = {"scan_clause": scan_clause}
            post_response = session.post(post_url, data=post_data, headers=post_headers)
            
            # 5. Return JSON to frontend
            self.send_response(post_response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # Allow CORS for our frontend
            self.end_headers()
            self.wfile.write(post_response.content)

        except Exception as e:
            self.send_error(500, str(e))

    def handle_pdh_data(self):
        url = "https://chartink.com/screener/copy-cpr-by-kgs-r1-pdh-broken-1344"
        try:
            session = requests.Session()
            
            # 1. Fetch main page
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://chartink.com/"
            }
            response = session.get(url, headers=headers)
            
            if response.status_code != 200:
                self.send_error(500, f"Chartink fetch failed: {response.status_code}")
                return

            # 2. Extract CSRF Token
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if not csrf_meta:
                self.send_error(500, "Could not find CSRF token")
                return
            csrf_token = csrf_meta['content']

            # 3. Extract scan_json -> scan_clause
            scan_json_match = re.search(r':scan-json=\'([^\']+)\'', response.text)
            if not scan_json_match:
                 scan_json_match = re.search(r':scan-json="([^"]+)"', response.text)
            
            if not scan_json_match:
                self.send_error(500, "Could not extract scan_json")
                return

            import html
            scan_json_str = html.unescape(scan_json_match.group(1))
            scan_data = json.loads(scan_json_str)
            
            # Use atlas_query or scan_clause string
            scan_clause = scan_data.get('scan_clause')
            if not scan_clause:
                scan_clause = scan_data.get('atlas_query')
            
            if not scan_clause:
                 self.send_error(500, "Could not find scan_clause or atlas_query")
                 return

            # 4. POST to process
            post_url = "https://chartink.com/screener/process"
            post_headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-CSRF-TOKEN": csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://chartink.com",
                "Referer": url,
            }
            
            post_data = {"scan_clause": scan_clause}
            post_response = session.post(post_url, data=post_data, headers=post_headers)
            
            # 5. Return JSON to frontend
            self.send_response(post_response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # Allow CORS for our frontend
            self.end_headers()
            self.wfile.write(post_response.content)

        except Exception as e:
            self.send_error(500, str(e))

    def handle_swing_data(self):
        url = "https://chartink.com/screener/swing-trade-breakout-strategy-10-20-gains"
        try:
            session = requests.Session()
            
            # 1. Fetch main page
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": "https://chartink.com/"
            }
            response = session.get(url, headers=headers)
            
            if response.status_code != 200:
                self.send_error(500, f"Chartink fetch failed: {response.status_code}")
                return

            # 2. Extract CSRF Token
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if not csrf_meta:
                self.send_error(500, "Could not find CSRF token")
                return
            csrf_token = csrf_meta['content']

            # 3. Extract scan_json -> scan_clause
            scan_json_match = re.search(r':scan-json=\'([^\']+)\'', response.text)
            if not scan_json_match:
                 scan_json_match = re.search(r':scan-json="([^"]+)"', response.text)
            
            if not scan_json_match:
                self.send_error(500, "Could not extract scan_json")
                return

            import html
            scan_json_str = html.unescape(scan_json_match.group(1))
            scan_data = json.loads(scan_json_str)
            
            # Use atlas_query or scan_clause string
            scan_clause = scan_data.get('scan_clause')
            if not scan_clause:
                scan_clause = scan_data.get('atlas_query')
            
            if not scan_clause:
                 self.send_error(500, "Could not find scan_clause or atlas_query")
                 return

            # 4. POST to process
            post_url = "https://chartink.com/screener/process"
            post_headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-CSRF-TOKEN": csrf_token,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://chartink.com",
                "Referer": url,
            }
            
            post_data = {"scan_clause": scan_clause}
            post_response = session.post(post_url, data=post_data, headers=post_headers)
            
            # 5. Return JSON to frontend
            self.send_response(post_response.status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # Allow CORS for our frontend
            self.end_headers()
            self.wfile.write(post_response.content)

        except Exception as e:
            self.send_error(500, str(e))

    def handle_chartink_page(self, path):
        # Fetch the specific scanner page
        url = f"{CHARTINK_BASE}{path}"
        print(f"Proxying Page: {url}")
        try:
            # Use a session for the initial page load to get initial cookies
            session = requests.Session()
            headers = self.get_forward_headers()
            headers['Referer'] = f"{CHARTINK_BASE}/"
            
            response = session.get(url, headers=headers, allow_redirects=True, timeout=15)
            
            if 'text/html' not in response.headers.get('Content-Type', ''):
                self.handle_proxy_request('GET')
                return

            content = response.text
            
            # Inject CSS to hide only site-wide clutter and fix layout
            css_injection = '''
            <style>
                /* Hide only site-wide Chartink UI (Nav, Footer, Ads) */
                nav, .navbar, .navbar-wrapper, footer, .footer, 
                .adsbygoogle, .sidebar-wrapper, .sidebar, .breadcrumbs-wrapper,
                .share-icons, .share-button, .modal-backdrop, .modal { 
                    display: none !important; 
                }
                
                /* Layout fixes to make it look native and clean */
                html, body { 
                    background-color: #f8fafc !important; 
                    margin: 0 !important; 
                    padding: 0 !important;
                    overflow: auto !important;
                    height: auto !important;
                    min-height: 100% !important;
                    font-family: 'Inter', sans-serif !important;
                }
                
                .wrapper, .main-panel, .content, .container, .container-fluid { 
                    background-color: transparent !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    width: 100% !important;
                    max-width: 100% !important;
                    box-shadow: none !important;
                    border: none !important;
                }
                
                /* Fix for the Purple Alert Section visibility */
                .alert-purple {
                    background-color: #f3e8ff !important;
                    border: 1px solid #e9d5ff !important;
                    color: #6b21a8 !important;
                    border-radius: 12px !important;
                    padding: 15px 20px !important;
                    margin-bottom: 20px !important;
                }
                
                .alert-purple button, .alert-purple .btn {
                    background-color: #6b21a8 !important;
                    color: #ffffff !important;
                    border: none !important;
                    border-radius: 8px !important;
                    padding: 6px 16px !important;
                    font-weight: 600 !important;
                }

                .alert-purple a {
                    color: #7e22ce !important;
                    text-decoration: underline !important;
                    font-weight: 600 !important;
                }

                /* Fix for "Scan passes all..." and Filters section */
                .magic-filters-wrapper, .scan-clause-wrapper {
                    background: #ffffff !important;
                    border: 1px solid #e2e8f0 !important;
                    border-radius: 16px !important;
                    padding: 20px !important;
                    margin-bottom: 20px !important;
                    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1) !important;
                }

                /* Table Styling - Professional Look */
                .card {
                    background: #ffffff !important;
                    border-radius: 16px !important;
                    border: 1px solid #e2e8f0 !important;
                    overflow: hidden !important;
                    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1) !important;
                }

                table { 
                    width: 100% !important; 
                    border-collapse: collapse !important; 
                }

                thead th {
                    background-color: #f8fafc !important;
                    color: #475569 !important;
                    font-weight: 700 !important;
                    text-transform: uppercase !important;
                    font-size: 12px !important;
                    padding: 16px !important;
                    border-bottom: 2px solid #f1f5f9 !important;
                }

                tbody td {
                    padding: 14px 16px !important;
                    color: #1e293b !important;
                    border-bottom: 1px solid #f1f5f9 !important;
                }

                /* Highlighting the Stock Name */
                tbody td a {
                    color: #2563eb !important;
                    font-weight: 600 !important;
                    text-decoration: none !important;
                }

                /* Fix for the "Loading" overlay */
                .loading-spinner-overlay {
                    display: none !important;
                }
                
                /* Ensure the table container is visible */
                .table-responsive, .dataTables_wrapper {
                    visibility: visible !important;
                    display: block !important;
                    opacity: 1 !important;
                }
            </style>
            '''
            
            # Inject AJAX fix script
            ajax_fix_script = r'''
            <script>
                (function() {
                    const originalFetch = window.fetch;
                    window.fetch = async function() {
                        if (arguments[0] && typeof arguments[0] === 'string') {
                            if (arguments[0].includes('chartink.com')) {
                                arguments[0] = arguments[0].replace(/https?:\/\/chartink\.com/, '');
                            }
                        }
                        const response = await originalFetch.apply(this, arguments);
                        
                        // Rewrite JSON responses if they contain chartink URLs
                        const contentType = response.headers.get('content-type');
                        if (contentType && contentType.includes('application/json')) {
                            const clone = response.clone();
                            try {
                                let text = await clone.text();
                                if (text.includes('chartink.com')) {
                                    text = text.replace(/https?:\/\/chartink\.com/g, '');
                                    return new Response(text, {
                                        status: response.status,
                                        statusText: response.statusText,
                                        headers: response.headers
                                    });
                                }
                            } catch (e) {}
                        }
                        return response;
                    };

                    const originalOpen = XMLHttpRequest.prototype.open;
                    XMLHttpRequest.prototype.open = function() {
                        if (arguments[1] && typeof arguments[1] === 'string') {
                            if (arguments[1].includes('chartink.com')) {
                                arguments[1] = arguments[1].replace(/https?:\/\/chartink\.com/, '');
                            }
                        }
                        return originalOpen.apply(this, arguments);
                    };
                    
                    // Also intercept script tags and other resource loading
                    const observer = new MutationObserver((mutations) => {
                        mutations.forEach((mutation) => {
                            mutation.addedNodes.forEach((node) => {
                                if (node.tagName === 'SCRIPT' && node.src && node.src.includes('chartink.com')) {
                                    node.src = node.src.replace(/https?:\/\/chartink\.com/, '');
                                }
                                if (node.tagName === 'LINK' && node.href && node.href.includes('chartink.com')) {
                                    node.href = node.href.replace(/https?:\/\/chartink\.com/, '');
                                }
                                if (node.tagName === 'IMG' && node.src && node.src.includes('chartink.com')) {
                                    node.src = node.src.replace(/https?:\/\/chartink\.com/, '');
                                }
                            });
                        });
                    });
                    observer.observe(document.documentElement, { childList: true, subtree: true });
                })();
            </script>
            '''
            
            # Replace Chartink URLs - both normal and escaped for JS
            content = content.replace('https://chartink.com', '')
            content = content.replace('http://chartink.com', '')
            content = content.replace('//chartink.com', '')
            content = content.replace('https:\\/\\/chartink.com', '')
            content = content.replace('http:\\/\\/chartink.com', '')
            
            # Remove any <base> tags that point to Chartink
            content = re.sub(r'<base[^>]+href=["\']https?://chartink\.com/?["\'][^>]*>', '', content, flags=re.IGNORECASE)
            
            # Also handle the base URL in meta tags if any
            content = content.replace('content="chartink.com"', 'content="localhost:8000"')
            
            if '</head>' in content:
                content = content.replace('<head>', '<head>' + ajax_fix_script + css_injection)
            else:
                content = ajax_fix_script + css_injection + content

            self.send_response(response.status_code)
            
            hop_by_hop = [
                'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 
                'te', 'trailers', 'transfer-encoding', 'upgrade', 'content-encoding', 
                'content-length', 'x-frame-options', 'content-security-policy', 
                'strict-transport-security', 'x-content-type-options', 'set-cookie'
            ]
            for k, v in response.headers.items():
                if k.lower() not in hop_by_hop:
                    self.send_header(k, v)
            
            self.send_header('X-Frame-Options', 'ALLOWALL')
            self.send_header('Access-Control-Allow-Origin', '*')
            
            # Forward cookies from the session
            for cookie in session.cookies:
                cookie_val = f"{cookie.name}={cookie.value}; Path=/"
                self.send_header('Set-Cookie', cookie_val)
            
            self.end_headers()
            self.wfile.write(content.encode('utf-8', errors='ignore'))
            
        except Exception as e:
            print(f"Error in handle_chartink_page: {e}")
            self.send_error(500, str(e))

    def handle_proxy_request(self, method):
        url = f"{CHARTINK_BASE}{self.path}"
        try:
            headers = self.get_forward_headers()
            
            data = None
            if method == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    data = self.rfile.read(content_length)

            # Use requests directly without a persistent session object on server side
            # The browser will manage the session via forwarded cookies
            if method == 'GET':
                response = requests.get(url, headers=headers, allow_redirects=False, timeout=15)
            else:
                response = requests.post(url, headers=headers, data=data, allow_redirects=False, timeout=15)
            
            print(f"Proxy Response [{response.status_code}]: {url}")
            self.send_response(response.status_code)
            
            # Forward headers but keep control over cookies and security
            hop_by_hop = [
                'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 
                'te', 'trailers', 'transfer-encoding', 'upgrade', 'content-encoding', 
                'content-length', 'x-frame-options', 'content-security-policy', 
                'strict-transport-security', 'x-content-type-options', 'set-cookie'
            ]
            for k, v in response.headers.items():
                if k.lower() not in hop_by_hop:
                    self.send_header(k, v)
            
            self.send_header('X-Frame-Options', 'ALLOWALL')
            self.send_header('Access-Control-Allow-Origin', '*')
            
            # Forward ALL Set-Cookie headers from Chartink to the browser
            # We must handle multiple Set-Cookie headers correctly
            if 'Set-Cookie' in response.headers:
                # requests might have combined them with commas
                cookies = response.raw.headers.getlist('Set-Cookie')
                for cookie in cookies:
                    # Strip domain/secure/samesite for local compatibility
                    c = re.sub(r'Domain=[^;]+;?\s*', '', cookie, flags=re.IGNORECASE)
                    c = re.sub(r'Secure;?\s*', '', c, flags=re.IGNORECASE)
                    c = re.sub(r'SameSite=[^;]+;?\s*', '', c, flags=re.IGNORECASE)
                    self.send_header('Set-Cookie', c)
            
            self.end_headers()
            
            content = response.content
            content_type = response.headers.get('Content-Type', '').lower()
            
            if any(t in content_type for t in ['javascript', 'json', 'text/html', 'text/css']):
                try:
                    text = content.decode('utf-8', errors='ignore')
                    text = text.replace('https://chartink.com', '')
                    text = text.replace('http://chartink.com', '')
                    text = text.replace('//chartink.com', '')
                    text = text.replace('https:\\/\\/chartink.com', '')
                    text = text.replace('http:\\/\\/chartink.com', '')
                    content = text.encode('utf-8')
                except:
                    pass
                    
            self.wfile.write(content)
            
        except Exception as e:
            print(f"Proxy Error for {url}: {e}")
            self.send_error(500, str(e))

    def get_forward_headers(self):
        headers = {}
        # Forward specific headers
        headers['User-Agent'] = self.headers.get('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        headers['Accept'] = self.headers.get('Accept', '*/*')
        headers['Accept-Language'] = self.headers.get('Accept-Language', 'en-US,en;q=0.9')
        headers['Accept-Encoding'] = 'identity' # Disable compression to allow string replacement
        
        if 'Origin' in self.headers:
            headers['Origin'] = CHARTINK_BASE
        
        # Referer logic
        if 'Referer' in self.headers:
            ref = self.headers['Referer']
            # If the referer is local, map it to Chartink
            if any(host in ref for host in ['localhost', '127.0.0.1', 'serveo']):
                # Extract the path from the local referer
                parsed_ref = urllib.parse.urlparse(ref)
                ref_path = parsed_ref.path
                if ref_path.startswith('/screener/'):
                    headers['Referer'] = f"{CHARTINK_BASE}{ref_path}"
                elif 'swing-scanner.html' in ref_path:
                    headers['Referer'] = f"{CHARTINK_BASE}/screener/swing-trade-breakout-strategy-10-20-gains"
                elif 'stock-option-screener.html' in ref_path:
                    headers['Referer'] = f"{CHARTINK_BASE}/screener/top-gainers-f-o-7"
                else:
                    headers['Referer'] = CHARTINK_BASE
            else:
                headers['Referer'] = ref
        else:
             headers['Referer'] = CHARTINK_BASE

        # Forward AJAX and Security headers
        for h in ['X-CSRF-TOKEN', 'X-Requested-With', 'Content-Type', 'Cookie', 'X-XSRF-TOKEN']:
            if h in self.headers:
                headers[h] = self.headers[h]
            
        return headers

    def forward_set_cookies(self, response_headers):
        # The requests.Response object headers can contain multiple Set-Cookie headers 
        # joined by commas, which is not standard.
        # However, we can use the response object directly if we have access to it?
        # Let's try to get them from the raw headers if available.
        # But handle_proxy_request doesn't have the response object here.
        # Let's adjust handle_proxy_request to pass the response object.
        pass

if __name__ == '__main__':
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    # Create the server
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        print(f"Serving on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass