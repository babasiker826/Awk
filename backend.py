from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import requests
import json
import re
import time
from datetime import datetime
import urllib.parse
import html

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
CORS(app)

# Global bilgi mesajları
INFO_TELEGRAM = "t.me/f3system"
INFO_ALT = "apileri bilerek saklamadım orospu cocukları))))9"

# Custom headers for all external API requests
EXTERNAL_API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "DNT": "1"
}

def fix_turkish_characters(text):
    """Türkçe karakterleri düzelt"""
    if not text:
        return text
    
    # HTML entity'leri decode et
    text = html.unescape(text)
    
    # Karakter düzeltmeleri
    char_map = {
        'Ã§': 'ç', 'Ã‡': 'Ç',
        'ÄŸ': 'ğ', 'Äž': 'Ğ',
        'Ä±': 'ı', 'Ä°': 'İ',
        'Ã¶': 'ö', 'Ã–': 'Ö',
        'ÅŸ': 'ş', 'Åž': 'Ş',
        'Ã¼': 'ü', 'Ãœ': 'Ü',
        'ÃŽ': 'İ', 'Ã®': 'i',
        'Ã¢': 'â', 'Ã‚': 'Â',
        'Ã»': 'û', 'Ã›': 'Û'
    }
    
    for wrong, correct in char_map.items():
        text = text.replace(wrong, correct)
    
    return text

# Enhanced response headers for our API
def add_response_headers(response, api_name, response_time=None):
    """Add custom headers to API responses"""
    response.headers['X-API-Name'] = api_name
    response.headers['X-API-Version'] = '2.0'
    response.headers['X-Developer'] = 'CROOS Checker'
    response.headers['X-Contact'] = 't.me/DemirKocs'
    
    if response_time:
        response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        response.headers['X-Backend-API-Time'] = f"{response_time:.3f}s"
    
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

# Helper functions
def validate_tc(tc):
    if not tc or not re.match(r'^\d{11}$', tc):
        return False
    return True

def validate_gsm(gsm):
    if not re.match(r'^5\d{9}$', gsm):
        return False
    return True

def validate_ip(ip):
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_adresno(adresno):
    if not re.match(r'^\d{10}$', adresno):
        return False
    return True

def rate_limit():
    current_time = time.time()
    if 'last_request' in session:
        if current_time - session['last_request'] < 1:
            return False
    session['last_request'] = current_time
    return True

def make_external_request(url, method='GET', timeout=30, retries=2):
    """Make external API request with retry logic"""
    for attempt in range(retries + 1):
        try:
            start_time = time.time()
            
            # Özel header'lar
            headers = {
                **EXTERNAL_API_HEADERS,
                "Referer": "https://zyrdaware.xyz/",
                "Origin": "https://zyrdaware.xyz"
            }
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout, verify=True)
            else:
                response = requests.post(url, headers=headers, timeout=timeout, verify=True)
            
            response_time = time.time() - start_time
            
            # Eğer içerik boşsa
            if not response.content:
                raise Exception("Empty response from API")
            
            # Yanıtı kontrol et
            response.raise_for_status()
            
            # JSON decode et
            data = response.json()
            return data, response_time
            
        except requests.exceptions.Timeout:
            if attempt == retries:
                raise Exception(f"Timeout after {retries+1} attempts")
            time.sleep(1 * (attempt + 1))
        except requests.exceptions.RequestException as e:
            if attempt == retries:
                raise Exception(f"Request failed: {str(e)}")
            time.sleep(1 * (attempt + 1))
        except json.JSONDecodeError as e:
            if attempt == retries:
                raise Exception(f"JSON decode error: {str(e)}")
            time.sleep(1 * (attempt + 1))
    
    raise Exception("Max retries exceeded")

# 1. Ad Soyad Sorgu - FIXED
@app.route('/Api/adsoyad.php')
def adsoyad_api():
    start_time = time.time()
    
    if not rate_limit():
        response = jsonify({
            "info": INFO_ALT,
            "error": "Çok hızlı istek! Lütfen bekleyin.",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'adsoyad', time.time() - start_time), 429
    
    ad = request.args.get('ad', '')
    soyad = request.args.get('soyad', '')
    il = request.args.get('il', '')
    ilce = request.args.get('ilce', '')
    
    if not ad:
        response = jsonify({
            "info": INFO_ALT,
            "error": "Lütfen ?ad= parametresini girin!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'adsoyad', time.time() - start_time), 400
    
    # URL oluştur
    base_url = "https://zyrdaware.xyz/api/adsoyad"
    params = {
        "auth": "t.me/zyrdaware",
        "ad": ad
    }
    
    if soyad:
        params["soyad"] = soyad
    if il:
        params["il"] = il
    if ilce:
        params["ilce"] = ilce
    
    try:
        # URL encode yap
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url = f"{base_url}?{query_string}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        api_start = time.time()
        response = requests.get(url, headers=headers, timeout=45)
        response_time = time.time() - api_start
        
        if response.status_code != 200:
            raise Exception(f"API returned status code: {response.status_code}")
        
        # JSON decode et
        data = response.json()
        
        output_data = []
        if "veri" in data and isinstance(data["veri"], list):
            for kisi in data["veri"]:
                output_data.append({
                    "TC": fix_turkish_characters(kisi.get("tc", "")),
                    "ADI": fix_turkish_characters(kisi.get("adi", "")),
                    "SOYADI": fix_turkish_characters(kisi.get("soyadi", "")),
                    "DOGUMTARIHI": fix_turkish_characters(kisi.get("dogumTarihi", "")),
                    "NUFUSIL": fix_turkish_characters(kisi.get("nufusIl", "")),
                    "NUFUSILCE": fix_turkish_characters(kisi.get("nufusIlce", "")),
                    "ANNEADI": fix_turkish_characters(kisi.get("anneAdi", "")),
                    "ANNETC": fix_turkish_characters(kisi.get("anneTc", "")),
                    "BABAADI": fix_turkish_characters(kisi.get("babaAdi", "")),
                    "BABATC": fix_turkish_characters(kisi.get("babaTc", ""))
                })
        
        output = {
            "info": INFO_ALT,
            "apiSahibi": "f3system",  # Burayı değiştirdik
            "success": data.get("success", "true"),
            "number": data.get("kayitSayisi", data.get("number", len(output_data))),
            "sure": data.get("sure", ""),
            "data": output_data,
            "backend_response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        response = jsonify(output)
        return add_response_headers(response, 'adsoyad', time.time() - start_time)
        
    except Exception as e:
        response = jsonify({
            "info": INFO_ALT,
            "error": f"API hatası: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'adsoyad', time.time() - start_time), 500

# 2. TC Sorgu - FIXED
@app.route('/Api/tc.php')
def tc_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            "info": INFO_TELEGRAM,
            "error": "Lütfen ?tc= parametresi girin!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tc', time.time() - start_time), 400
    
    if not validate_tc(tc):
        response = jsonify({
            "info": INFO_TELEGRAM,
            "error": "Geçersiz TC kimlik numarası!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tc', time.time() - start_time), 400
    
    url = f"https://zyrdaware.xyz/api/tcpro?auth=t.me/zyrdaware&tc={tc}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        api_start = time.time()
        response = requests.get(url, headers=headers, timeout=40)
        response_time = time.time() - api_start
        
        if response.status_code != 200:
            raise Exception(f"API returned status code: {response.status_code}")
        
        data = response.json()
        
        if "veri" in data and isinstance(data["veri"], list) and len(data["veri"]) > 0:
            veri = data["veri"][0]
            output = {
                "info": INFO_TELEGRAM,
                "apiSahibi": "f3system",  # Burayı değiştirdik
                "data": {
                    "TC": fix_turkish_characters(veri.get("TC", veri.get("tc", ""))),
                    "ADI": fix_turkish_characters(veri.get("AD", veri.get("adi", ""))),
                    "SOYADI": fix_turkish_characters(veri.get("SOYAD", veri.get("soyadi", ""))),
                    "DOGUMTARIHI": fix_turkish_characters(veri.get("DOGUMTARIHI", veri.get("dogumTarihi", ""))),
                    "NUFUSIL": fix_turkish_characters(veri.get("ADRESIL", veri.get("nufusIl", ""))),
                    "NUFUSILCE": fix_turkish_characters(veri.get("ADRESILCE", veri.get("nufusIlce", ""))),
                    "ANNEADI": fix_turkish_characters(veri.get("ANNEADI", veri.get("anneAdi", ""))),
                    "ANNETC": fix_turkish_characters(veri.get("ANNETC", veri.get("anneTc", ""))),
                    "BABAADI": fix_turkish_characters(veri.get("BABAADI", veri.get("babaAdi", ""))),
                    "BABATC": fix_turkish_characters(veri.get("BABATC", veri.get("babaTc", "")))
                },
                "backend_response_time": f"{response_time:.3f}s",
                "timestamp": datetime.now().isoformat()
            }
            response = jsonify(output)
            return add_response_headers(response, 'tc', time.time() - start_time)
        else:
            response = jsonify({
                "info": INFO_TELEGRAM,
                "apiSahibi": "f3system",  # Burayı değiştirdik
                "error": "TC kimlik numarası bulunamadı!",
                "timestamp": datetime.now().isoformat()
            })
            return add_response_headers(response, 'tc', time.time() - start_time), 404
            
    except Exception as e:
        response = jsonify({
            "info": INFO_TELEGRAM,
            "apiSahibi": "f3system",  # Burayı değiştirdik
            "error": f"API hatası: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tc', time.time() - start_time), 500

# 3. Aile Sorgu - FIXED
@app.route('/Api/aile.php')
def aile_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            "info": INFO_ALT,
            "apiSahibi": "f3system",
            "error": "Lütfen ?tc= parametresi girin!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile', time.time() - start_time), 400
    
    if not validate_tc(tc):
        response = jsonify({
            "info": INFO_ALT,
            "apiSahibi": "f3system",
            "error": "Geçersiz TC kimlik numarası!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile', time.time() - start_time), 400
    
    url = f"https://zyrdaware.xyz/api/aile?auth=t.me/zyrdaware&tc={tc}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        api_start = time.time()
        response = requests.get(url, headers=headers, timeout=45)
        response_time = time.time() - api_start
        
        if response.status_code != 200:
            raise Exception(f"API returned status code: {response.status_code}")
        
        data = response.json()
        
        if "veri" not in data or not isinstance(data["veri"], list):
            response = jsonify({
                "info": "t.me/DemirKocs",
                "apiSahibi": "f3system",
                "error": "API'den beklenen veri yapısı alınamadı!",
                "timestamp": datetime.now().isoformat()
            })
            return add_response_headers(response, 'aile', time.time() - start_time), 500
        
        aile = []
        for kisi in data["veri"]:
            aile.append({
                "Yakınlık": fix_turkish_characters(kisi.get("yakinlik", "")),
                "TC": fix_turkish_characters(kisi.get("tc", "")),
                "AD": fix_turkish_characters(kisi.get("adi", "")),
                "SOYAD": fix_turkish_characters(kisi.get("soyadi", "")),
                "DOGUMTARIHI": fix_turkish_characters(kisi.get("dogumTarihi", ""))
            })
        
        output = {
            "info": INFO_ALT,
            "apiSahibi": "f3system",
            "success": data.get("success", "true"),
            "number": data.get("number", len(aile)),
            "data": aile,
            "backend_response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        response = jsonify(output)
        return add_response_headers(response, 'aile', time.time() - start_time)
        
    except Exception as e:
        response = jsonify({
            "info": INFO_ALT,
            "apiSahibi": "f3system",
            "error": f"API hatası: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile', time.time() - start_time), 500

# 4. TC-GSM Sorgu - FIXED
@app.route('/Api/tcgsm.php')
def tcgsm_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "apiSahibi": "f3system",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tcgsm', time.time() - start_time), 400
    
    if not validate_tc(tc):
        response = jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "apiSahibi": "f3system",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tcgsm', time.time() - start_time), 400
    
    if not rate_limit():
        response = jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "apiSahibi": "f3system",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tcgsm', time.time() - start_time), 429
    
    url = f"https://zyrdaware.xyz/api/tcgsm?auth=t.me/zyrdaware&tc={tc}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        api_start = time.time()
        response = requests.get(url, headers=headers, timeout=50)
        response_time = time.time() - api_start
        
        data = response.json()
        veri = data.get("veri", [])
        
        # Türkçe karakter düzeltme
        for item in veri:
            if isinstance(item, dict):
                for key in item:
                    if isinstance(item[key], str):
                        item[key] = fix_turkish_characters(item[key])
        
        output = {
            "info": "nerde beles oraya yerles dimi piiiccc",
            "apiSahibi": "f3system",
            "veri": veri,
            "backend_response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        response = jsonify(output)
        return add_response_headers(response, 'tcgsm', time.time() - start_time)
        
    except Exception:
        response = jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "apiSahibi": "f3system",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tcgsm', time.time() - start_time), 500

# 5. GSM-TC Sorgu - FIXED
@app.route('/Api/gsmtc.php')
def gsmtc_api():
    start_time = time.time()
    
    gsm = request.args.get('gsm', '')
    
    if not gsm:
        response = jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "apiSahibi": "f3system",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'gsmtc', time.time() - start_time), 400
    
    if not validate_gsm(gsm):
        response = jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "apiSahibi": "f3system",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'gsmtc', time.time() - start_time), 400
    
    if not rate_limit():
        response = jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "apiSahibi": "f3system",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'gsmtc', time.time() - start_time), 429
    
    url = f"https://zyrdaware.xyz/api/gsmtc?auth=t.me/zyrdaware&gsm={gsm}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        api_start = time.time()
        response = requests.get(url, headers=headers, timeout=50)
        response_time = time.time() - api_start
        
        data = response.json()
        
        veri = []
        if "veri" in data and isinstance(data["veri"], list):
            for item in data["veri"]:
                veri.append({
                    "gsm": gsm,
                    "tc": fix_turkish_characters(str(item.get('tc') or item.get('TC') or item.get('Tc') or ''))
                })
        
        output = {
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "apiSahibi": "f3system",
            "veri": veri,
            "backend_response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        response = jsonify(output)
        return add_response_headers(response, 'gsmtc', time.time() - start_time)
        
    except Exception:
        response = jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "apiSahibi": "f3system",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'gsmtc', time.time() - start_time), 500

# 6. Adres Sorgu - FIXED
@app.route('/Api/adres.php')
def adres_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            "info": INFO_TELEGRAM,
            "apiSahibi": "f3system",
            "error": "Lütfen ?tc= parametresi girin!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'adres', time.time() - start_time), 400
    
    url = f"https://hold-periodically-file-oriented.trycloudflare.com/Api/adres.php?tc={tc}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        api_start = time.time()
        response = requests.get(url, headers=headers, timeout=60)
        response_time = time.time() - api_start
        
        if response.status_code != 200:
            raise Exception(f"API returned status code: {response.status_code}")
        
        data = response.json()
        
        if "success" in data:
            del data["success"]
        
        output = {
            "info": INFO_TELEGRAM,
            "apiSahibi": "f3system",
            "data": {
                "KimlikNo": fix_turkish_characters(data.get("data", {}).get("TC", "")),
                "GuncelAdres": fix_turkish_characters(data.get("data", {}).get("ADRES", "")),
                "Adres2024": fix_turkish_characters(data.get("data", {}).get("ADRES2024", "")),
                "Adres2023": fix_turkish_characters(data.get("data", {}).get("ADRES2023", "")),
                "Adres2017": fix_turkish_characters(data.get("data", {}).get("ADRES2017", "")),
                "Adres2015": fix_turkish_characters(data.get("data", {}).get("ADRES2015", "")),
                "Adres2009": fix_turkish_characters(data.get("data", {}).get("ADRES2009", ""))
            },
            "backend_response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        response = jsonify(output)
        return add_response_headers(response, 'adres', time.time() - start_time)
        
    except Exception as e:
        response = jsonify({
            "info": INFO_TELEGRAM,
            "apiSahibi": "f3system",
            "error": f"API hatası: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'adres', time.time() - start_time), 500

# 7. Sülale Sorgu - FIXED
@app.route('/Api/sulale.php')
def sulale_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            "info": INFO_ALT,
            "apiSahibi": "f3system",
            "error": "Lütfen ?tc= parametresi girin!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'sulale', time.time() - start_time), 400
    
    url = f"https://sorgusuz.world/api/s%C3%BClale.php?tc={tc}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        api_start = time.time()
        response = requests.get(url, headers=headers, timeout=60)
        response_time = time.time() - api_start
        
        if response.status_code != 200:
            raise Exception(f"API returned status code: {response.status_code}")
        
        data = response.json()
        
        if "data" not in data or not isinstance(data["data"], list):
            response = jsonify({
                "info": INFO_ALT,
                "apiSahibi": "f3system",
                "error": "API'den beklenen veri yapısı alınamadı!",
                "timestamp": datetime.now().isoformat()
            })
            return add_response_headers(response, 'sulale', time.time() - start_time), 500
        
        sulale = []
        for kisi in data["data"]:
            sulale.append({
                "YAKINLIK": fix_turkish_characters(kisi.get("Yakinlik", "")),
                "TC": fix_turkish_characters(kisi.get("TC", "")),
                "ADI": fix_turkish_characters(kisi.get("Ad", "")),
                "SOYADI": fix_turkish_characters(kisi.get("Soyad", "")),
                "DogumTarihi": fix_turkish_characters(kisi.get("DogumTarihi", "")),
                "NufusIl": fix_turkish_characters(kisi.get("AdresIl", "")),
                "NufusIlce": fix_turkish_characters(kisi.get("AdresIlce", "")),
                "AnneIsim": fix_turkish_characters(kisi.get("AnneAdi", "")),
                "AnneKimlikNo": fix_turkish_characters(kisi.get("AnneTC", "")),
                "BabaIsim": fix_turkish_characters(kisi.get("BabaAdi", "")),
                "BabaKimlikNo": fix_turkish_characters(kisi.get("BabaTC", ""))
            })
        
        output = {
            "info": INFO_ALT,
            "apiSahibi": "f3system",
            "success": data.get("success", "true"),
            "yarramkadardata": sulale,
            "backend_response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        response = jsonify(output)
        return add_response_headers(response, 'sulale', time.time() - start_time)
        
    except Exception as e:
        response = jsonify({
            "info": INFO_ALT,
            "apiSahibi": "f3system",
            "error": f"API hatası: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'sulale', time.time() - start_time), 500

# 8. AdresNo Sorgu - FIXED
@app.route('/Api/adresno.php')
def adresno_api():
    start_time = time.time()
    
    adresNo = request.args.get('adresNo', '')
    
    if not adresNo:
        response = jsonify({
            'hata': 'Geçersiz adresNo. 10 haneli rakam olmalıdır.',
            'ornek': 'sıze ornek yok oclar fsffsfsmköslsxfsfsf',
            'apiSahibi': 'f3system',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'adresno', time.time() - start_time), 400
    
    if not validate_adresno(adresNo):
        response = jsonify({
            'hata': 'Geçersiz adresNo. 10 haneli rakam olmalıdır.',
            'ornek': 'sıze ornek yok oclar fsffsfsmköslsxfsfsf',
            'apiSahibi': 'f3system',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'adresno', time.time() - start_time), 400
    
    url = f"https://dijital.gib.gov.tr/apigateway/api/nologin/mernis/adres-bilgisi-getir-with-adres-no?adresNo={adresNo}"
    
    try:
        headers = {
            "User-Agent": "GibAdresApi/2.0 (+https://crooschecker.com)",
            "Accept": "application/json"
        }
        
        api_start = time.time()
        response_req = requests.get(url, headers=headers, timeout=90, verify=True)
        response_time = time.time() - api_start
        response_req.raise_for_status()
        
        data = response_req.json()
        
        if "adresAciklama" in data:
            output = {
                'basarili': True,
                'apiSahibi': 'f3system',
                'adresNo': adresNo,
                'tamAdres': fix_turkish_characters(data['adresAciklama']),
                'mahalle': fix_turkish_characters(data.get('mahAd')),
                'caddeSokak': fix_turkish_characters(data.get('csbmAd')),
                'disKapiNo': data.get('disKapiNo'),
                'icKapiNo': data.get('icKapiNo'),
                'backend_response_time': f"{response_time:.3f}s",
                'timestamp': datetime.now().isoformat()
            }
            response = jsonify(output)
            return add_response_headers(response, 'adresno', time.time() - start_time)
        else:
            response = jsonify({
                'basarili': False,
                'apiSahibi': 'f3system',
                'hata': 'Bu adresNo ile kayıtlı adres bulunamadı.',
                'timestamp': datetime.now().isoformat()
            })
            return add_response_headers(response, 'adresno', time.time() - start_time), 404
            
    except requests.exceptions.Timeout:
        response = jsonify({
            'hata': 'GİB sunucusundan 90 saniye içinde yanıt alınamadı (timeout).',
            'apiSahibi': 'f3system',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'adresno', time.time() - start_time), 504
    except Exception as e:
        response = jsonify({
            'hata': f'GİB bağlantı hatası: {str(e)}',
            'apiSahibi': 'f3system',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'adresno', time.time() - start_time), 502

# 9. IP Sorgu - FIXED
@app.route('/Api/ip.php')
def ip_api():
    start_time = time.time()
    
    ip = request.args.get('ip', '')
    
    if not ip:
        ip = request.remote_addr
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('HTTP_CF_CONNECTING_IP'):
            ip = request.headers.get('HTTP_CF_CONNECTING_IP')
    
    if not validate_ip(ip):
        response = jsonify({
            'status': 'error',
            'message': 'Geçersiz IP adresi formatı',
            'info': INFO_TELEGRAM,
            'apiSahibi': 'f3system',
            'received_ip': ip,
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'ip', time.time() - start_time), 400
    
    apis = {
        'ipapi': f"https://ipapi.co/{ip}/json/",
        'ipinfo': f"https://ipinfo.io/{ip}/json",
        'ipapi_com': f"http://ip-api.com/json/{ip}"
    }
    
    try:
        # İlk API'yi dene
        first_api = 'ipapi_com'
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        api_start = time.time()
        response = requests.get(apis[first_api], headers=headers, timeout=10)
        first_response_time = time.time() - api_start
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                standardized_data = {
                    'info': INFO_TELEGRAM,
                    'apiSahibi': 'f3system',
                    'status': 'success',
                    'query': ip,
                    'data': {
                        'ip': data.get('query', ip),
                        'city': fix_turkish_characters(data.get('city')),
                        'region': fix_turkish_characters(data.get('regionName')),
                        'country': fix_turkish_characters(data.get('country')),
                        'isp': fix_turkish_characters(data.get('isp')),
                        'timezone': data.get('timezone'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'as': data.get('as')
                    },
                    'backend_response_time': f"{first_response_time:.3f}s",
                    'backend_service': first_api,
                    'timestamp': datetime.now().isoformat()
                }
                response = jsonify(standardized_data)
                return add_response_headers(response, 'ip', time.time() - start_time)
    except:
        pass
    
    # Diğer API'leri dene
    for service, url in apis.items():
        if service == first_api:
            continue
            
        try:
            api_start = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            response_time = time.time() - api_start
            
            if response.status_code == 200:
                data = response.json()
                
                if service == 'ipapi':
                    standardized_data = {
                        'info': INFO_TELEGRAM,
                        'apiSahibi': 'f3system',
                        'status': 'success',
                        'query': ip,
                        'data': {
                            'ip': data.get('ip', ip),
                            'city': fix_turkish_characters(data.get('city')),
                            'region': fix_turkish_characters(data.get('region')),
                            'country': fix_turkish_characters(data.get('country_name', data.get('country'))),
                            'country_code': data.get('country_code'),
                            'isp': fix_turkish_characters(data.get('org')),
                            'timezone': data.get('timezone'),
                            'latitude': data.get('latitude'),
                            'longitude': data.get('longitude')
                        },
                        'backend_response_time': f"{response_time:.3f}s",
                        'backend_service': service,
                        'timestamp': datetime.now().isoformat()
                    }
                    response = jsonify(standardized_data)
                    return add_response_headers(response, 'ip', time.time() - start_time)
                elif service == 'ipinfo':
                    standardized_data = {
                        'info': INFO_TELEGRAM,
                        'apiSahibi': 'f3system',
                        'status': 'success',
                        'query': ip,
                        'data': {
                            'ip': data.get('ip', ip),
                            'city': fix_turkish_characters(data.get('city')),
                            'region': fix_turkish_characters(data.get('region')),
                            'country': fix_turkish_characters(data.get('country')),
                            'isp': fix_turkish_characters(data.get('org')),
                            'timezone': data.get('timezone'),
                            'location': data.get('loc', '').split(',') if data.get('loc') else None
                        },
                        'backend_response_time': f"{response_time:.3f}s",
                        'backend_service': service,
                        'timestamp': datetime.now().isoformat()
                    }
                    response = jsonify(standardized_data)
                    return add_response_headers(response, 'ip', time.time() - start_time)
        except:
            continue
    
    # Tüm API'ler başarısız oldu
    response = {
        'info': INFO_TELEGRAM,
        'apiSahibi': 'f3system',
        'status': 'partial_error',
        'message': 'API servislerinden tam veri alınamadı',
        'query': ip,
        'local_data': {
            'ip': ip,
            'user_agent': request.headers.get('User-Agent'),
            'language': request.headers.get('Accept-Language'),
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        'timestamp': datetime.now().isoformat()
    }
    response = jsonify(response)
    return add_response_headers(response, 'ip', time.time() - start_time), 502

# 10. Aile Sorgu (çocuklar) - FIXED
@app.route('/Api/ailecocuk.php')
def aile_cocuk_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            'status': 'error',
            'message': 'TC kimlik numarası gerekli',
            'apiSahibi': 'f3system',
            'usage': '?tc=11111111110',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile_cocuk', time.time() - start_time), 400
    
    if not validate_tc(tc):
        response = jsonify({
            'status': 'error',
            'message': 'Geçersiz TC kimlik numarası formatı (11 rakam olmalı)',
            'apiSahibi': 'f3system',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile_cocuk', time.time() - start_time), 400
    
    url = f'https://hold-periodically-file-oriented.trycloudflare.com/Api/cocuk.php?tc={tc}'
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        api_start = time.time()
        response = requests.get(url, headers=headers, timeout=60)
        response_time = time.time() - api_start
        response.raise_for_status()
        
        data = response.json()
        
        # Türkçe karakter düzeltme
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], str):
                    data[key] = fix_turkish_characters(data[key])
                elif isinstance(data[key], list):
                    for item in data[key]:
                        if isinstance(item, dict):
                            for subkey in item:
                                if isinstance(item[subkey], str):
                                    item[subkey] = fix_turkish_characters(item[subkey])
        
        # backend_response_time ekle
        if isinstance(data, dict):
            data['backend_response_time'] = f"{response_time:.3f}s"
            data['apiSahibi'] = 'f3system'
            data['timestamp'] = datetime.now().isoformat()
        
        response = jsonify(data)
        return add_response_headers(response, 'aile_cocuk', time.time() - start_time)
        
    except Exception as e:
        response = jsonify({
            'status': 'error',
            'apiSahibi': 'f3system',
            'message': 'API bağlantı hatası',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile_cocuk', time.time() - start_time), 500

# 11. İşyeri Sorgu - FIXED
@app.route('/Api/isyeri.php')
def isyeri_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            'status': False,
            'message': 'TC kimlik numarası gerekli',
            'apiSahibi': 'f3system',
            'example': '?tc=15689993550',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'isyeri', time.time() - start_time), 400
    
    if not validate_tc(tc):
        response = jsonify({
            'status': False,
            'message': 'Geçersiz TC kimlik numarası formatı (11 rakam olmalı)',
            'apiSahibi': 'f3system',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'isyeri', time.time() - start_time), 400
    
    url = f'https://hold-periodically-file-oriented.trycloudflare.com/Mernis/Api/isyeri.php?tc={tc}'
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        api_start = time.time()
        response = requests.get(url, headers=headers, timeout=75, verify=False)
        response_time = time.time() - api_start
        response.raise_for_status()
        
        try:
            data = response.json()
            
            # Türkçe karakter düzeltme
            if isinstance(data, dict):
                for key in data:
                    if isinstance(data[key], str):
                        data[key] = fix_turkish_characters(data[key])
                    elif isinstance(data[key], list):
                        for item in data[key]:
                            if isinstance(item, dict):
                                for subkey in item:
                                    if isinstance(item[subkey], str):
                                        item[subkey] = fix_turkish_characters(item[subkey])
            
            # backend_response_time ekle
            if isinstance(data, dict):
                data['backend_response_time'] = f"{response_time:.3f}s"
                data['apiSahibi'] = 'f3system'
                data['timestamp'] = datetime.now().isoformat()
            
            response = jsonify(data)
            return add_response_headers(response, 'isyeri', time.time() - start_time)
        except json.JSONDecodeError:
            response = jsonify({
                'status': False,
                'apiSahibi': 'f3system',
                'message': 'API geçersiz JSON yanıtı döndürdü',
                'backend_response_time': f"{response_time:.3f}s",
                'raw_response': response.text[:500],
                'timestamp': datetime.now().isoformat()
            })
            return add_response_headers(response, 'isyeri', time.time() - start_time), 502
            
    except Exception as e:
        response = jsonify({
            'status': False,
            'apiSahibi': 'f3system',
            'message': 'API bağlantı hatası',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'isyeri', time.time() - start_time), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'apiSahibi': 'f3system',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0',
        'apis_available': 11
    })

# 12. Ana HTML Sayfası için endpoint
@app.route('/Api')
def api_dashboard():
    return '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/png" href="favicon.png">
    <title>f3system Free API | Türkiye API Servisleri</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Montserrat:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <style>
        :root {
            --bg-color: #000000;
            --text-color: #ffffff;
            --secondary-color: #aaaaaa;
            --accent-color: #ffffff;
            --border-color: #333333;
            --card-bg: rgba(20, 20, 20, 0.8);
            --hover-color: #252525;
            --glow-color: rgba(255, 255, 255, 0.7);
            --primary-color: #4CAF50;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Montserrat', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }

        .space {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: 0;
            overflow: hidden;
        }

        .star {
            position: absolute;
            width: 2px;
            height: 2px;
            background: white;
            border-radius: 50%;
            animation: moveStar linear infinite;
        }

        @keyframes moveStar {
            0% { transform: translateY(0) translateX(0); opacity: 1; }
            100% { transform: translateY(100vh) translateX(-100vw); opacity: 0; }
        }

        .shooting-star {
            position: absolute;
            color: white;
            font-size: 10px;
            opacity: 0.9;
            transform: rotate(45deg);
            text-shadow: -5px -5px 0 rgba(255,255,255,0.2), -10px -10px 0 rgba(255,255,255,0.1);
            animation: shootStar 2s linear;
        }

        @keyframes shootStar {
            0% { top: -50px; left: -50px; opacity: 0.9; }
            100% { top: 100%; left: 100%; opacity: 0; }
        }

        .container {
            max-width: 1200px;
            width: 90%;
            margin: auto;
            padding: 40px 20px;
            position: relative;
            z-index: 1;
        }

        .header {
            margin-bottom: 50px;
            text-align: center;
        }

        h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 4rem;
            font-weight: 900;
            margin-bottom: 10px;
            letter-spacing: 3px;
            text-transform: uppercase;
            position: relative;
            display: inline-block;
            text-shadow: 0 0 10px var(--glow-color), 0 0 20px var(--glow-color), 0 0 30px var(--glow-color);
            animation: glitch 5s infinite;
        }

        @keyframes glitch {
            0%, 100% { transform: translate(0); }
            20% { transform: translate(-2px, 2px); }
            40% { transform: translate(-2px, -2px); }
            60% { transform: translate(2px, 2px); }
            80% { transform: translate(2px, -2px); }
        }

        .subtitle {
            font-size: 1.5rem;
            color: var(--primary-color);
            font-weight: 600;
            margin-top: 20px;
            text-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }

        .api-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 50px;
        }

        .api-card {
            background-color: var(--card-bg);
            padding: 25px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            text-align: left;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(5px);
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
        }

        .api-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background-color: var(--primary-color);
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }

        .api-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(76, 175, 80, 0.2);
            background-color: rgba(30, 30, 30, 0.9);
            border-color: var(--primary-color);
        }

        .api-card h3 {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--primary-color);
            text-shadow: 0 0 5px rgba(76, 175, 80, 0.5);
        }

        .api-card h3 i {
            color: var(--primary-color);
            text-shadow: 0 0 5px rgba(76, 175, 80, 0.7);
        }

        .api-url {
            font-family: monospace;
            font-size: 0.9rem;
            color: var(--secondary-color);
            word-break: break-all;
            margin-bottom: 20px;
            padding: 12px;
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 6px;
            border: 1px solid var(--border-color);
        }

        .api-url:hover {
            border-color: var(--primary-color);
        }

        .button-group {
            display: flex;
            gap: 10px;
            margin-top: auto;
        }

        .btn {
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s ease;
            cursor: pointer;
            border: none;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 0.9rem;
            font-family: 'Orbitron', sans-serif;
        }

        .btn-primary {
            background-color: var(--primary-color);
            color: white;
            flex: 1;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }

        .btn-primary:hover {
            background-color: #45a049;
            box-shadow: 0 0 15px rgba(76, 175, 80, 0.7);
        }

        .btn-secondary {
            background-color: transparent;
            color: var(--text-color);
            border: 1px solid var(--border-color);
            flex: 1;
        }

        .btn-secondary:hover {
            background-color: var(--border-color);
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        }

        .info-section {
            padding: 30px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            background-color: var(--card-bg);
            margin-bottom: 30px;
            text-align: left;
            backdrop-filter: blur(5px);
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
        }

        .info-section h3 {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--primary-color);
            text-shadow: 0 0 5px rgba(76, 175, 80, 0.5);
        }

        .info-section p {
            color: var(--secondary-color);
            font-size: 1rem;
            line-height: 1.7;
        }

        .contact-section {
            display: flex;
            flex-direction: column;
            gap: 20px;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            background-color: var(--card-bg);
            backdrop-filter: blur(5px);
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
        }

        .contact-text {
            text-align: center;
        }

        .contact-text h3 {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--primary-color);
            text-shadow: 0 0 5px rgba(76, 175, 80, 0.5);
        }

        .contact-text p {
            color: var(--secondary-color);
        }

        .contact-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }

        .contact-btn {
            background-color: var(--primary-color);
            color: white;
            padding: 12px 25px;
            border-radius: 6px;
            font-weight: 500;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
            font-family: 'Orbitron', sans-serif;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }

        .contact-btn:hover {
            background-color: #45a049;
            box-shadow: 0 0 15px rgba(76, 175, 80, 0.7);
        }

        .api-status {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
            font-size: 0.9rem;
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .status-online {
            background-color: var(--primary-color);
            box-shadow: 0 0 10px var(--primary-color);
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        @media (max-width: 768px) {
            h1 {
                font-size: 2.5rem;
            }

            .container {
                padding: 20px;
            }

            .api-container {
                grid-template-columns: 1fr;
                gap: 20px;
            }

            .api-card {
                padding: 20px;
            }

            .contact-buttons {
                flex-direction: column;
                align-items: center;
            }

            .contact-btn {
                width: 100%;
                max-width: 250px;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="space" id="space"></div>

    <div class="container">
        <div class="header">
            <h1>f3system Free API</h1>
            <p class="subtitle">Türkiye'nin En Kapsamlı Ücretsiz API Servisleri</p>
            <div class="api-status">
                <span class="status-indicator status-online"></span>
                <span>Tüm API'ler Aktif | Ücretsiz Kullanım | 11 Farklı Sorgu</span>
            </div>
        </div>

        <div class="api-container">
            <div class="api-card">
                <h3><i class="fas fa-user"></i> Ad Soyad Sorgu</h3>
                <div class="api-url" id="api-url-1">/Api/adsoyad.php?ad=ALİ&soyad=YILMAZ&il=DİYARBAKIR&ilce=BİSMİL</div>
                <div class="button-group">
                    <a href="/Api/adsoyad.php?ad=ALİ&soyad=YILMAZ&il=DİYARBAKIR&ilce=BİSMİL" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/adsoyad.php?ad=ALİ&soyad=YILMAZ&il=DİYARBAKIR&ilce=BİSMİL')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-id-card"></i> TC Sorgu</h3>
                <div class="api-url" id="api-url-2">/Api/tc.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="/Api/tc.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/tc.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-users"></i> Aile Sorgu</h3>
                <div class="api-url" id="api-url-3">/Api/aile.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="/Api/aile.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/aile.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-phone"></i> TC-GSM Sorgu</h3>
                <div class="api-url" id="api-url-4">/Api/tcgsm.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="/Api/tcgsm.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/tcgsm.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-phone-alt"></i> GSM-TC Sorgu</h3>
                <div class="api-url" id="api-url-5">/Api/gsmtc.php?gsm=5415722525</div>
                <div class="button-group">
                    <a href="/Api/gsmtc.php?gsm=5415722525" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/gsmtc.php?gsm=5415722525')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-map-marker-alt"></i> Adres Sorgu</h3>
                <div class="api-url" id="api-url-6">/Api/adres.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="/Api/adres.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/adres.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-family"></i> Sülale Sorgu</h3>
                <div class="api-url" id="api-url-7">/Api/sulale.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="/Api/sulale.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/sulale.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-home"></i> Adresno Sorgu</h3>
                <div class="api-url" id="api-url-8">/Api/adresno.php?adresNo=3212827459</div>
                <div class="button-group">
                    <a href="/Api/adresno.php?adresNo=3212827459" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/adresno.php?adresNo=3212827459')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-network-wired"></i> IP Sorgu</h3>
                <div class="api-url" id="api-url-9">/Api/ip.php?ip=8.8.8.8</div>
                <div class="button-group">
                    <a href="/Api/ip.php?ip=8.8.8.8" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/ip.php?ip=8.8.8.8')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-baby"></i> Çocuk Sorgu</h3>
                <div class="api-url" id="api-url-10">/Api/ailecocuk.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="/Api/ailecocuk.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/ailecocuk.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-building"></i> İşyeri Sorgu</h3>
                <div class="api-url" id="api-url-11">/Api/isyeri.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="/Api/isyeri.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/isyeri.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>
        </div>

        <div class="info-section">
            <h3><i class="fas fa-info-circle"></i> API Kullanım Bilgileri</h3>
            <p><strong>Versiyon:</strong> 2.0 | <strong>API Sahibi:</strong> f3system | <strong>Status:</strong> Aktif</p>
            <p><strong>Özellikler:</strong> Tüm API'ler ücretsiz, Türkçe karakter desteği, optimize edilmiş performans</p>
            <p><strong>Not:</strong> API'ler sadece eğitim ve geliştirme amaçlıdır. Kötüye kullanım durumunda erişim engellenebilir.</p>
            <p><strong>Limit:</strong> Saniyede 1 istek | <strong>Format:</strong> JSON</p>
        </div>

        <div class="contact-section">
            <div class="contact-text">
                <h3>İletişim & Destek</h3>
                <p>Sorularınız ve önerileriniz için Telegram'dan iletişime geçebilirsiniz.</p>
            </div>
            <div class="contact-buttons">
                <a href="https://t.me/f3system" target="_blank" class="contact-btn">
                    <i class="fab fa-telegram"></i> Telegram: @f3system
                </a>
                <a href="/health" target="_blank" class="contact-btn" style="background-color: #2196F3;">
                    <i class="fas fa-heartbeat"></i> Sistem Durumu
                </a>
            </div>
        </div>
    </div>

    <script>
        // Galaksi efekti
        const space = document.getElementById('space');
        for(let i=0; i<120; i++){
            const star = document.createElement('div');
            star.className = 'star';
            star.style.top = Math.random()*100+'%';
            star.style.left = Math.random()*100+'%';
            star.style.animationDuration = (Math.random()*5+5)+'s';
            space.appendChild(star);
        }

        setInterval(()=>{
            const shooting = document.createElement('div');
            shooting.className = 'shooting-star';
            shooting.innerHTML = '✦';
            shooting.style.top = Math.random()*50+'%';
            shooting.style.left = Math.random()*50+'%';
            space.appendChild(shooting);
            setTimeout(()=>shooting.remove(), 2500);
        }, 4000);

        // Link kopyalama
        async function copyLink(button, textToCopy) {
            const fullUrl = window.location.origin + textToCopy;
            try {
                await navigator.clipboard.writeText(fullUrl);
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="fas fa-check"></i> Kopyalandı!';
                button.style.backgroundColor = '#4CAF50';
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.style.backgroundColor = '';
                }, 2000);
            } catch {
                const originalHTML = button.innerHTML;
                button.innerHTML = '<i class="fas fa-exclamation-circle"></i> Hata!';
                button.style.backgroundColor = '#f44336';
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.style.backgroundColor = '';
                }, 2000);
            }
        }

        // URL'leri dinamik olarak güncelle
        document.addEventListener('DOMContentLoaded', function() {
            const baseUrl = window.location.origin;
            const apiUrls = [
                {id: 'api-url-1', url: '/Api/adsoyad.php?ad=ALİ&soyad=YILMAZ&il=DİYARBAKIR&ilce=BİSMİL'},
                {id: 'api-url-2', url: '/Api/tc.php?tc=11111111110'},
                {id: 'api-url-3', url: '/Api/aile.php?tc=11111111110'},
                {id: 'api-url-4', url: '/Api/tcgsm.php?tc=11111111110'},
                {id: 'api-url-5', url: '/Api/gsmtc.php?gsm=5415722525'},
                {id: 'api-url-6', url: '/Api/adres.php?tc=11111111110'},
                {id: 'api-url-7', url: '/Api/sulale.php?tc=11111111110'},
                {id: 'api-url-8', url: '/Api/adresno.php?adresNo=3212827459'},
                {id: 'api-url-9', url: '/Api/ip.php?ip=8.8.8.8'},
                {id: 'api-url-10', url: '/Api/ailecocuk.php?tc=11111111110'},
                {id: 'api-url-11', url: '/Api/isyeri.php?tc=11111111110'}
            ];

            apiUrls.forEach(api => {
                const element = document.getElementById(api.id);
                if (element) {
                    element.textContent = baseUrl + api.url;
                }

                // Butonların href'lerini de güncelle
                const button = element?.closest('.api-card')?.querySelector('.btn-primary');
                if (button) {
                    button.href = baseUrl + api.url;
                }
            });
        });
    </script>
</body>
</html>
'''

# Ana sayfa
@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>f3system Free API - Ana Sayfa</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            text-align: center;
            max-width: 800px;
            padding: 40px;
            background: rgba(30, 30, 30, 0.9);
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(76, 175, 80, 0.3);
        }
        
        h1 {
            font-size: 3.5rem;
            margin-bottom: 20px;
            color: #4CAF50;
            text-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }
        
        h2 {
            font-size: 2rem;
            margin-bottom: 30px;
            color: #ffffff;
        }
        
        .description {
            font-size: 1.2rem;
            line-height: 1.6;
            margin-bottom: 40px;
            color: #cccccc;
        }
        
        .buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 15px 30px;
            border-radius: 10px;
            text-decoration: none;
            font-size: 1.1rem;
            font-weight: bold;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(76, 175, 80, 0.6);
        }
        
        .btn-secondary {
            background: transparent;
            color: #4CAF50;
            border: 2px solid #4CAF50;
        }
        
        .btn-secondary:hover {
            background: rgba(76, 175, 80, 0.1);
            transform: translateY(-3px);
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 40px;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #4CAF50;
            display: block;
        }
        
        .stat-label {
            font-size: 1rem;
            color: #cccccc;
        }
        
        @media (max-width: 768px) {
            h1 {
                font-size: 2.5rem;
            }
            
            h2 {
                font-size: 1.5rem;
            }
            
            .container {
                padding: 20px;
            }
            
            .buttons {
                flex-direction: column;
                align-items: center;
            }
            
            .btn {
                width: 100%;
                max-width: 300px;
                justify-content: center;
            }
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <h1>f3system Free API</h1>
        <h2>Türkiye'nin En Kapsamlı Ücretsiz API Platformu</h2>
        
        <div class="description">
            <p>11 farklı sorgu API'si ile kişi, aile, adres, IP ve işyeri bilgilerine hızlı ve güvenli erişim.</p>
            <p>Tüm API'ler tamamen ücretsiz, Türkçe karakter desteği ile optimize edilmiş performans sunar.</p>
        </div>
        
        <div class="buttons">
            <a href="/Api" class="btn btn-primary">
                <i class="fas fa-rocket"></i> API Listesini Gör
            </a>
            <a href="https://t.me/f3system" target="_blank" class="btn btn-secondary">
                <i class="fab fa-telegram"></i> Telegram'dan Ulaş
            </a>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <span class="stat-number">11</span>
                <span class="stat-label">API Servisi</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">100%</span>
                <span class="stat-label">Ücretsiz</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">7/24</span>
                <span class="stat-label">Aktif</span>
            </div>
        </div>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
