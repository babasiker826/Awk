from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import requests
import json
import re
import time
from datetime import datetime
import urllib.parse
import concurrent.futures

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
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "Origin": "http://localhost:5000",
    "Referer": "http://localhost:5000/",
    "DNT": "1",
    "Sec-GPC": "1"
}

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
            if method.upper() == 'GET':
                response = requests.get(url, headers=EXTERNAL_API_HEADERS, timeout=timeout)
            else:
                response = requests.post(url, headers=EXTERNAL_API_HEADERS, timeout=timeout)
            
            response_time = time.time() - start_time
            response.raise_for_status()
            return response, response_time
            
        except requests.exceptions.Timeout:
            if attempt == retries:
                raise Exception(f"Timeout after {retries+1} attempts")
            time.sleep(1 * (attempt + 1))  # Exponential backoff
        except requests.exceptions.RequestException as e:
            if attempt == retries:
                raise Exception(f"Request failed: {str(e)}")
            time.sleep(1 * (attempt + 1))
    
    raise Exception("Max retries exceeded")

# 1. Ad Soyad Sorgu
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
    
    url = f"https://zyrdaware.xyz/api/adsoyad?auth=t.me/zyrdaware&ad={urllib.parse.quote(ad)}"
    if soyad:
        url += f"&soyad={urllib.parse.quote(soyad)}"
    if il:
        url += f"&il={urllib.parse.quote(il)}"
    if ilce:
        url += f"&ilce={urllib.parse.quote(ilce)}"
    
    try:
        external_response, response_time = make_external_request(url, timeout=45)
        data = external_response.json()
        
        output_data = []
        if "veri" in data and isinstance(data["veri"], list):
            for kisi in data["veri"]:
                output_data.append({
                    "TC": kisi.get("tc", ""),
                    "ADI": kisi.get("adi", ""),
                    "SOYADI": kisi.get("soyadi", ""),
                    "DOGUMTARIHI": kisi.get("dogumTarihi", ""),
                    "NUFUSIL": kisi.get("nufusIl", ""),
                    "NUFUSILCE": kisi.get("nufusIlce", ""),
                    "ANNEADI": kisi.get("anneAdi", ""),
                    "ANNETC": kisi.get("anneTc", ""),
                    "BABAADI": kisi.get("babaAdi", ""),
                    "BABATC": kisi.get("babaTc", "")
                })
        
        output = {
            "info": INFO_ALT,
            "success": data.get("success", "true"),
            "number": data.get("number", len(output_data)),
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

# 2. TC Sorgu
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
        external_response, response_time = make_external_request(url, timeout=40)
        data = external_response.json()
        
        if "veri" in data and isinstance(data["veri"], list) and len(data["veri"]) > 0:
            veri = data["veri"][0]
            output = {
                "info": INFO_TELEGRAM,
                "data": {
                    "TC": veri.get("TC", ""),
                    "ADI": veri.get("AD", ""),
                    "SOYADI": veri.get("SOYAD", ""),
                    "DOGUMTARIHI": veri.get("DOGUMTARIHI", ""),
                    "NUFUSIL": veri.get("ADRESIL", ""),
                    "NUFUSILCE": veri.get("ADRESILCE", ""),
                    "ANNEADI": veri.get("ANNEADI", ""),
                    "ANNETC": veri.get("ANNETC", ""),
                    "BABAADI": veri.get("BABAADI", ""),
                    "BABATC": veri.get("BABATC", "")
                },
                "backend_response_time": f"{response_time:.3f}s",
                "timestamp": datetime.now().isoformat()
            }
            response = jsonify(output)
            return add_response_headers(response, 'tc', time.time() - start_time)
        else:
            response = jsonify({
                "info": INFO_TELEGRAM,
                "error": "TC kimlik numarası bulunamadı!",
                "timestamp": datetime.now().isoformat()
            })
            return add_response_headers(response, 'tc', time.time() - start_time), 404
            
    except Exception as e:
        response = jsonify({
            "info": INFO_TELEGRAM,
            "error": f"API hatası: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tc', time.time() - start_time), 500

# 3. Aile Sorgu
@app.route('/Api/aile.php')
def aile_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            "info": INFO_ALT,
            "error": "Lütfen ?tc= parametresi girin!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile', time.time() - start_time), 400
    
    if not validate_tc(tc):
        response = jsonify({
            "info": INFO_ALT,
            "error": "Geçersiz TC kimlik numarası!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile', time.time() - start_time), 400
    
    url = f"https://zyrdaware.xyz/api/aile?auth=t.me/zyrdaware&tc={tc}"
    
    try:
        external_response, response_time = make_external_request(url, timeout=45)
        data = external_response.json()
        
        if "veri" not in data or not isinstance(data["veri"], list):
            response = jsonify({
                "info": "t.me/DemirKocs",
                "error": "API'den beklenen veri yapısı alınamadı!",
                "timestamp": datetime.now().isoformat()
            })
            return add_response_headers(response, 'aile', time.time() - start_time), 500
        
        aile = []
        for kisi in data["veri"]:
            aile.append({
                "Yakınlık": kisi.get("yakinlik", ""),
                "TC": kisi.get("tc", ""),
                "AD": kisi.get("adi", ""),
                "SOYAD": kisi.get("soyadi", ""),
                "DOGUMTARIHI": kisi.get("dogumTarihi", "")
            })
        
        output = {
            "info": INFO_ALT,
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
            "error": f"API hatası: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile', time.time() - start_time), 500

# 4. TC-GSM Sorgu
@app.route('/Api/tcgsm.php')
def tcgsm_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tcgsm', time.time() - start_time), 400
    
    if not validate_tc(tc):
        response = jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tcgsm', time.time() - start_time), 400
    
    if not rate_limit():
        response = jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tcgsm', time.time() - start_time), 429
    
    url = f"https://zyrdaware.xyz/api/tcgsm?auth=t.me/zyrdaware&tc={tc}"
    
    try:
        external_response, response_time = make_external_request(url, timeout=50)
        data = external_response.json()
        veri = data.get("veri", [])
        
        output = {
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": veri,
            "backend_response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        response = jsonify(output)
        return add_response_headers(response, 'tcgsm', time.time() - start_time)
        
    except Exception:
        response = jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'tcgsm', time.time() - start_time), 500

# 5. GSM-TC Sorgu
@app.route('/Api/gsmtc.php')
def gsmtc_api():
    start_time = time.time()
    
    gsm = request.args.get('gsm', '')
    
    if not gsm:
        response = jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'gsmtc', time.time() - start_time), 400
    
    if not validate_gsm(gsm):
        response = jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'gsmtc', time.time() - start_time), 400
    
    if not rate_limit():
        response = jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'gsmtc', time.time() - start_time), 429
    
    url = f"https://zyrdaware.xyz/api/gsmtc?auth=t.me/zyrdaware&gsm={gsm}"
    
    try:
        external_response, response_time = make_external_request(url, timeout=50)
        data = external_response.json()
        
        veri = []
        if "veri" in data and isinstance(data["veri"], list):
            for item in data["veri"]:
                veri.append({
                    "gsm": gsm,
                    "tc": item.get('tc') or item.get('TC') or item.get('Tc') or ''
                })
        
        output = {
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": veri,
            "backend_response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        response = jsonify(output)
        return add_response_headers(response, 'gsmtc', time.time() - start_time)
        
    except Exception:
        response = jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": [],
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'gsmtc', time.time() - start_time), 500

# 6. Adres Sorgu
@app.route('/Api/adres.php')
def adres_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            "info": INFO_TELEGRAM,
            "error": "Lütfen ?tc= parametresi girin!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'adres', time.time() - start_time), 400
    
    url = f"https://hold-periodically-file-oriented.trycloudflare.com/Api/adres.php?tc={tc}"
    
    try:
        external_response, response_time = make_external_request(url, timeout=60)
        data = external_response.json()
        
        if "success" in data:
            del data["success"]
        
        output = {
            "info": INFO_TELEGRAM,
            "data": {
                "KimlikNo": data.get("data", {}).get("TC", ""),
                "GuncelAdres": data.get("data", {}).get("ADRES", ""),
                "Adres2024": data.get("data", {}).get("ADRES2024", ""),
                "Adres2023": data.get("data", {}).get("ADRES2023", ""),
                "Adres2017": data.get("data", {}).get("ADRES2017", ""),
                "Adres2015": data.get("data", {}).get("ADRES2015", ""),
                "Adres2009": data.get("data", {}).get("ADRES2009", "")
            },
            "backend_response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        
        response = jsonify(output)
        return add_response_headers(response, 'adres', time.time() - start_time)
        
    except Exception as e:
        response = jsonify({
            "info": INFO_TELEGRAM,
            "error": f"API hatası: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'adres', time.time() - start_time), 500

# 7. Sülale Sorgu
@app.route('/Api/sulale.php')
def sulale_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            "info": INFO_ALT,
            "error": "Lütfen ?tc= parametresi girin!",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'sulale', time.time() - start_time), 400
    
    url = f"https://sorgusuz.world/api/s%C3%BClale.php?tc={tc}"
    
    try:
        external_response, response_time = make_external_request(url, timeout=60)
        data = external_response.json()
        
        if "data" not in data or not isinstance(data["data"], list):
            response = jsonify({
                "info": INFO_ALT,
                "error": "API'den beklenen veri yapısı alınamadı!",
                "timestamp": datetime.now().isoformat()
            })
            return add_response_headers(response, 'sulale', time.time() - start_time), 500
        
        sulale = []
        for kisi in data["data"]:
            sulale.append({
                "YAKINLIK": kisi.get("Yakinlik", ""),
                "TC": kisi.get("TC", ""),
                "ADI": kisi.get("Ad", ""),
                "SOYADI": kisi.get("Soyad", ""),
                "DogumTarihi": kisi.get("DogumTarihi", ""),
                "NufusIl": kisi.get("AdresIl", ""),
                "NufusIlce": kisi.get("AdresIlce", ""),
                "AnneIsim": kisi.get("AnneAdi", ""),
                "AnneKimlikNo": kisi.get("AnneTC", ""),
                "BabaIsim": kisi.get("BabaAdi", ""),
                "BabaKimlikNo": kisi.get("BabaTC", "")
            })
        
        output = {
            "info": INFO_ALT,
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
            "error": f"API hatası: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        return add_response_headers(response, 'sulale', time.time() - start_time), 500

# 8. AdresNo Sorgu
@app.route('/Api/adresno.php')
def adresno_api():
    start_time = time.time()
    
    adresNo = request.args.get('adresNo', '')
    
    if not adresNo:
        response = jsonify({
            'hata': 'Geçersiz adresNo. 10 haneli rakam olmalıdır.',
            'ornek': 'sıze ornek yok oclar fsffsfsmköslsxfsfsf',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'adresno', time.time() - start_time), 400
    
    if not validate_adresno(adresNo):
        response = jsonify({
            'hata': 'Geçersiz adresNo. 10 haneli rakam olmalıdır.',
            'ornek': 'sıze ornek yok oclar fsffsfsmköslsxfsfsf',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'adresno', time.time() - start_time), 400
    
    url = f"https://dijital.gib.gov.tr/apigateway/api/nologin/mernis/adres-bilgisi-getir-with-adres-no?adresNo={adresNo}"
    
    try:
        headers = {
            **EXTERNAL_API_HEADERS,
            "User-Agent": "GibAdresApi/2.0 (+https://crooschecker.com)"
        }
        
        start_external = time.time()
        response_req = requests.get(url, headers=headers, timeout=90, verify=True)
        response_time = time.time() - start_external
        response_req.raise_for_status()
        
        data = response_req.json()
        
        if "adresAciklama" in data:
            output = {
                'basarili': True,
                'adresNo': adresNo,
                'tamAdres': data['adresAciklama'],
                'mahalle': data.get('mahAd'),
                'caddeSokak': data.get('csbmAd'),
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
                'hata': 'Bu adresNo ile kayıtlı adres bulunamadı.',
                'timestamp': datetime.now().isoformat()
            })
            return add_response_headers(response, 'adresno', time.time() - start_time), 404
            
    except requests.exceptions.Timeout:
        response = jsonify({
            'hata': 'GİB sunucusundan 90 saniye içinde yanıt alınamadı (timeout).',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'adresno', time.time() - start_time), 504
    except Exception as e:
        response = jsonify({
            'hata': f'GİB bağlantı hatası: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'adresno', time.time() - start_time), 502

# 9. IP Sorgu - Enhanced with async calls
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
            'received_ip': ip,
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'ip', time.time() - start_time), 400
    
    apis = {
        'ipapi': f"https://ipapi.co/{ip}/json/",
        'ipinfo': f"https://ipinfo.io/{ip}/json",
        'ipapi_com': f"http://ip-api.com/json/{ip}"
    }
    
    def fetch_api(service, url):
        try:
            api_start = time.time()
            response = requests.get(url, headers=EXTERNAL_API_HEADERS, timeout=15)
            api_time = time.time() - api_start
            return {
                'service': service,
                'data': response.json() if response.status_code == 200 else None,
                'status_code': response.status_code,
                'response_time': api_time
            }
        except Exception as e:
            return {
                'service': service,
                'data': None,
                'error': str(e),
                'status_code': 500
            }
    
    # Try to get data from first API quickly
    try:
        first_api = 'ipapi_com'
        api_start = time.time()
        response = requests.get(apis[first_api], headers=EXTERNAL_API_HEADERS, timeout=10)
        first_response_time = time.time() - api_start
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                standardized_data = {
                    'info': INFO_TELEGRAM,
                    'status': 'success',
                    'query': ip,
                    'data': {
                        'ip': data.get('query', ip),
                        'city': data.get('city'),
                        'region': data.get('regionName'),
                        'country': data.get('country'),
                        'isp': data.get('isp'),
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
    
    # If first API fails, try others with threading
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_api = {executor.submit(fetch_api, service, url): service 
                        for service, url in apis.items()}
        
        for future in concurrent.futures.as_completed(future_to_api, timeout=20):
            service = future_to_api[future]
            try:
                results[service] = future.result(timeout=10)
            except Exception:
                results[service] = {'service': service, 'data': None, 'status_code': 500}
    
    final_data = None
    used_service = None
    backend_time = None
    
    for service in ['ipapi', 'ipinfo', 'ipapi_com']:
        if service in results and results[service].get('data'):
            final_data = results[service]['data']
            used_service = service
            backend_time = results[service].get('response_time', 0)
            break
    
    if final_data:
        standardized_data = {
            'info': INFO_TELEGRAM,
            'status': 'success',
            'query': ip,
            'data': {},
            'backend_response_time': f"{backend_time:.3f}s" if backend_time else "N/A",
            'backend_service': used_service,
            'timestamp': datetime.now().isoformat()
        }
        
        if used_service == 'ipapi':
            standardized_data['data'] = {
                'ip': final_data.get('ip', ip),
                'city': final_data.get('city'),
                'region': final_data.get('region'),
                'country': final_data.get('country_name', final_data.get('country')),
                'country_code': final_data.get('country_code'),
                'isp': final_data.get('org'),
                'timezone': final_data.get('timezone'),
                'latitude': final_data.get('latitude'),
                'longitude': final_data.get('longitude')
            }
        elif used_service == 'ipinfo':
            standardized_data['data'] = {
                'ip': final_data.get('ip', ip),
                'city': final_data.get('city'),
                'region': final_data.get('region'),
                'country': final_data.get('country'),
                'isp': final_data.get('org'),
                'timezone': final_data.get('timezone'),
                'location': final_data.get('loc', '').split(',') if final_data.get('loc') else None
            }
        elif used_service == 'ipapi_com' and final_data.get('status') == 'success':
            standardized_data['data'] = {
                'ip': final_data.get('query', ip),
                'city': final_data.get('city'),
                'region': final_data.get('regionName'),
                'country': final_data.get('country'),
                'isp': final_data.get('isp'),
                'timezone': final_data.get('timezone'),
                'latitude': final_data.get('lat'),
                'longitude': final_data.get('lon'),
                'as': final_data.get('as')
            }
        
        response = jsonify(standardized_data)
        return add_response_headers(response, 'ip', time.time() - start_time)
    else:
        response = {
            'info': INFO_TELEGRAM,
            'status': 'partial_error',
            'message': 'API servislerinden tam veri alınamadı',
            'query': ip,
            'local_data': {
                'ip': ip,
                'user_agent': request.headers.get('User-Agent'),
                'language': request.headers.get('Accept-Language'),
                'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'api_status': {service: results.get(service, {}).get('status_code', 'timeout') 
                          for service in apis},
            'timestamp': datetime.now().isoformat()
        }
        response = jsonify(response)
        return add_response_headers(response, 'ip', time.time() - start_time), 502

# 10. Aile Sorgu (çocuklar)
@app.route('/Apiaile.php')
def aile_cocuk_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            'status': 'error',
            'message': 'TC kimlik numarası gerekli',
            'usage': '?tc=11111111110',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile_cocuk', time.time() - start_time), 400
    
    if not validate_tc(tc):
        response = jsonify({
            'status': 'error',
            'message': 'Geçersiz TC kimlik numarası formatı (11 rakam olmalı)',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile_cocuk', time.time() - start_time), 400
    
    url = f'https://hold-periodically-file-oriented.trycloudflare.com/Api/cocuk.php?tc={tc}'
    
    try:
        external_response, response_time = make_external_request(url, timeout=60)
        data = external_response.json()
        
        # Add backend response time to response
        if isinstance(data, dict):
            data['backend_response_time'] = f"{response_time:.3f}s"
            data['timestamp'] = datetime.now().isoformat()
        
        response = jsonify(data)
        return add_response_headers(response, 'aile_cocuk', time.time() - start_time)
        
    except Exception as e:
        response = jsonify({
            'status': 'error',
            'message': 'API bağlantı hatası',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'aile_cocuk', time.time() - start_time), 500

# 11. İşyeri Sorgu
@app.route('/Mernis/Api/isyeri.php')
def isyeri_api():
    start_time = time.time()
    
    tc = request.args.get('tc', '')
    
    if not tc:
        response = jsonify({
            'status': False,
            'message': 'TC kimlik numarası gerekli',
            'example': '?tc=15689993550',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'isyeri', time.time() - start_time), 400
    
    if not validate_tc(tc):
        response = jsonify({
            'status': False,
            'message': 'Geçersiz TC kimlik numarası formatı (11 rakam olmalı)',
            'timestamp': datetime.now().isoformat()
        })
        return add_response_headers(response, 'isyeri', time.time() - start_time), 400
    
    url = f'https://hold-periodically-file-oriented.trycloudflare.com/Mernis/Api/isyeri.php?tc={tc}'
    
    try:
        external_response, response_time = make_external_request(url, timeout=75)
        
        try:
            data = external_response.json()
            if isinstance(data, dict):
                data['backend_response_time'] = f"{response_time:.3f}s"
                data['timestamp'] = datetime.now().isoformat()
            
            response = jsonify(data)
            return add_response_headers(response, 'isyeri', time.time() - start_time)
        except json.JSONDecodeError:
            response = jsonify({
                'status': False,
                'message': 'API geçersiz JSON yanıtı döndürdü',
                'backend_response_time': f"{response_time:.3f}s",
                'raw_response': external_response.text[:500],
                'timestamp': datetime.now().isoformat()
            })
            return add_response_headers(response, 'isyeri', time.time() - start_time), 502
            
    except Exception as e:
        response = jsonify({
            'status': False,
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
    <title>CROOS Checker | API v2.0</title>
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
            --success-color: #4CAF50;
            --warning-color: #ff9800;
            --error-color: #f44336;
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
            font-size: 1.2rem;
            color: var(--secondary-color);
            font-weight: 400;
            margin-top: 20px;
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
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
            background-color: var(--accent-color);
            box-shadow: 0 0 10px var(--glow-color);
        }

        .api-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(255, 255, 255, 0.2);
            background-color: rgba(30, 30, 30, 0.9);
        }

        .api-card h3 {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--accent-color);
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
        }

        .api-card h3 i {
            color: var(--accent-color);
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.7);
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

        .response-time {
            font-size: 0.8rem;
            color: var(--success-color);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 5px;
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
            background-color: var(--accent-color);
            color: var(--bg-color);
            flex: 1;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }

        .btn-primary:hover {
            background-color: #cccccc;
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.7);
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

        .btn-test {
            background-color: var(--warning-color);
            color: white;
            flex: 0.5;
        }

        .btn-test:hover {
            background-color: #e68900;
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
            color: var(--accent-color);
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
        }

        .info-section p {
            color: var(--secondary-color);
            font-size: 1rem;
            line-height: 1.7;
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-online {
            background-color: var(--success-color);
            box-shadow: 0 0 10px var(--success-color);
        }

        .status-warning {
            background-color: var(--warning-color);
            box-shadow: 0 0 10px var(--warning-color);
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
            color: var(--accent-color);
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
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
            background-color: var(--accent-color);
            color: var(--bg-color);
            padding: 12px 25px;
            border-radius: 6px;
            font-weight: 500;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
            font-family: 'Orbitron', sans-serif;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }

        .contact-btn:hover {
            background-color: #cccccc;
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.7);
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
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
            <h1>CROOS CHECKER v2.0</h1>
            <p class="subtitle">Gelişmiş API Servisleri - Optimize Edilmiş Performans</p>
            <p class="subtitle" style="font-size: 0.9rem; margin-top: 5px;">
                <span class="status-indicator status-online"></span> Sistem Çalışıyor | 
                <span id="current-time">--:--:--</span> | 
                Yanıt Süreleri: <span id="avg-response">Optimize Edildi</span>
            </p>
        </div>

        <div class="api-container">
            <!-- API Cards with test buttons -->
            <div class="api-card">
                <h3><i class="fas fa-user"></i> Ad Soyad Sorgu</h3>
                <div class="response-time"><i class="fas fa-clock"></i> Optimize Edildi (45s timeout)</div>
                <div class="api-url" id="api-url-1">/Api/adsoyad.php?ad=roket&soyad=atar&il=&ilce=</div>
                <div class="button-group">
                    <a href="/Api/adsoyad.php?ad=roket&soyad=atar&il=&ilce=" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, '/Api/adsoyad.php?ad=roket&soyad=atar&il=&ilce=')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                    <button onclick="testApi('adsoyad', 'ad=roket&soyad=atar')" class="btn btn-test">
                        <i class="fas fa-vial"></i> Test
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-id-card"></i> TC Sorgu</h3>
                <div class="response-time"><i class="fas fa-clock"></i> Optimize Edildi (40s timeout)</div>
                <div class="api-url" id="api-url-2">/Api/tc.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="/Api/tc.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, '/Api/tc.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                    <button onclick="testApi('tc', 'tc=11111111110')" class="btn btn-test">
                        <i class="fas fa-vial"></i> Test
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-users"></i> Aile Sorgu</h3>
                <div class="response-time"><i class="fas fa-clock"></i> Optimize Edildi (45s timeout)</div>
                <div class="api-url" id="api-url-3">/Api/aile.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="/Api/aile.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, '/Api/aile.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                    <button onclick="testApi('aile', 'tc=11111111110')" class="btn btn-test">
                        <i class="fas fa-vial"></i> Test
                    </button>
                </div>
            </div>

            <!-- Diğer API kartları aynı şekilde devam ediyor -->
            <!-- Kısalık için diğer kartları aynı pattern ile ekleyebilirsiniz -->
        </div>

        <div class="info-section">
            <h3><i class="fas fa-info-circle"></i> Sistem Bilgileri</h3>
            <p><strong>Versiyon:</strong> 2.0 | <strong>Optimizasyon:</strong> Aktif</p>
            <p><strong>Özellikler:</strong> Gelişmiş timeout yönetimi, retry mekanizması, header optimizasyonu, yanıt süresi takibi</p>
            <p><strong>Not:</strong> Tüm API'ler ücretsiz olarak sunulmaktadır. API'ler sadece eğitim amaçlıdır.</p>
        </div>

        <div class="contact-section">
            <div class="contact-text">
                <h3>İletişim & Destek</h3>
                <p>Sorularınız ve önerileriniz için iletişime geçebilirsiniz.</p>
            </div>
            <div class="contact-buttons">
                <a href="https://t.me/DemirKocs" target="_blank" class="contact-btn">
                    <i class="fab fa-telegram"></i> Telegram
                </a>
                <a href="/health" target="_blank" class="contact-btn" style="background-color: var(--success-color);">
                    <i class="fas fa-heartbeat"></i> Health Check
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

        // Saat güncelleme
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = 
                now.getHours().toString().padStart(2, '0') + ':' +
                now.getMinutes().toString().padStart(2, '0') + ':' +
                now.getSeconds().toString().padStart(2, '0');
        }
        setInterval(updateTime, 1000);
        updateTime();

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

        // API test fonksiyonu
        async function testApi(apiName, params) {
            const button = event.target;
            const originalHTML = button.innerHTML;
            button.innerHTML = '<div class="loading"></div>';
            button.disabled = true;
            
            try {
                const startTime = Date.now();
                const response = await fetch(`/Api/${apiName}.php?${params}`);
                const responseTime = Date.now() - startTime;
                
                if (response.ok) {
                    const data = await response.json();
                    button.innerHTML = `<i class="fas fa-check"></i> ${responseTime}ms`;
                    button.style.backgroundColor = '#4CAF50';
                    
                    // Yanıt bilgilerini göster
                    alert(`✅ API Test Başarılı!\n\nYanıt Süresi: ${responseTime}ms\nStatus: ${response.status}\nBackend Time: ${data.backend_response_time || 'N/A'}`);
                } else {
                    button.innerHTML = '<i class="fas fa-times"></i> Hata';
                    button.style.backgroundColor = '#f44336';
                    alert(`❌ API Test Başarısız!\n\nStatus: ${response.status}\n${response.statusText}`);
                }
            } catch (error) {
                button.innerHTML = '<i class="fas fa-times"></i> Hata';
                button.style.backgroundColor = '#f44336';
                alert(`❌ API Test Başarısız!\n\nHata: ${error.message}`);
            }
            
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.style.backgroundColor = '';
                button.disabled = false;
            }, 3000);
        }

        // URL'leri dinamik olarak güncelle
        document.addEventListener('DOMContentLoaded', function() {
            const baseUrl = window.location.origin;
            const apiUrls = [
                {id: 'api-url-1', url: '/Api/adsoyad.php?ad=roket&soyad=atar&il=&ilce='},
                {id: 'api-url-2', url: '/Api/tc.php?tc=11111111110'},
                {id: 'api-url-3', url: '/Api/aile.php?tc=11111111110'},
                {id: 'api-url-4', url: '/Api/tcgsm.php?tc=11111111110'},
                {id: 'api-url-5', url: '/Api/gsmtc.php?gsm=5415722525'},
                {id: 'api-url-6', url: '/Api/adres.php?tc=11111111110'},
                {id: 'api-url-7', url: '/Api/sulale.php?tc=11111111110'},
                {id: 'api-url-8', url: '/Api/adresno.php?adresNo=3212827459'},
                {id: 'api-url-9', url: '/Api/ip.php?ip=8.8.8.8'},
                {id: 'api-url-10', url: '/Apiaile.php?tc=11111111110'},
                {id: 'api-url-11', url: '/Mernis/Api/isyeri.php?tc=11111111110'}
            ];

            apiUrls.forEach(api => {
                const element = document.getElementById(api.id);
                if (element) {
                    element.textContent = baseUrl + api.url;
                }
            });
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
