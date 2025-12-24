from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import requests
import json
import re
import time
from datetime import datetime
import urllib.parse

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Session için gerekli
CORS(app)  # CORS izinleri

# Global bilgi mesajları
INFO_TELEGRAM = "t.me/DemirKocs"
INFO_ALT = "apileri bilerek saklamadım orospu cocukları))))9"

# Yardımcı fonksiyonlar
def validate_tc(tc):
    """TC kimlik numarası doğrulama"""
    if not tc or not re.match(r'^\d{11}$', tc):
        return False
    return True

def validate_gsm(gsm):
    """GSM numarası doğrulama"""
    if not re.match(r'^5\d{9}$', gsm):
        return False
    return True

def validate_ip(ip):
    """IP adresi doğrulama"""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_adresno(adresno):
    """Adres numarası doğrulama"""
    if not re.match(r'^\d{10}$', adresno):
        return False
    return True

def rate_limit():
    """Rate limiting kontrolü"""
    current_time = time.time()
    if 'last_request' in session:
        if current_time - session['last_request'] < 1:  # 1 saniye bekle
            return False
    session['last_request'] = current_time
    return True

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')  # HTML dosyasını ayrıca oluşturmanız gerekir

# API Endpoint'leri

# 1. Ad Soyad Sorgu
@app.route('/Api/adsoyad.php')
def adsoyad_api():
    if not rate_limit():
        return jsonify({
            "info": INFO_ALT,
            "error": "Çok hızlı istek! Lütfen bekleyin."
        }), 429
    
    ad = request.args.get('ad', '')
    soyad = request.args.get('soyad', '')
    il = request.args.get('il', '')
    ilce = request.args.get('ilce', '')
    
    if not ad:
        return jsonify({
            "info": INFO_ALT,
            "error": "Lütfen ?ad= parametresini girin!"
        }), 400
    
    # API URL oluştur
    url = f"https://zyrdaware.xyz/api/adsoyad?auth=t.me/zyrdaware&ad={urllib.parse.quote(ad)}"
    if soyad:
        url += f"&soyad={urllib.parse.quote(soyad)}"
    if il:
        url += f"&il={urllib.parse.quote(il)}"
    if ilce:
        url += f"&ilce={urllib.parse.quote(ilce)}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
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
            "data": output_data
        }
        
        return jsonify(output)
        
    except requests.RequestException as e:
        return jsonify({
            "info": INFO_ALT,
            "error": f"API bağlantı hatası: {str(e)}"
        }), 500
    except json.JSONDecodeError:
        return jsonify({
            "info": INFO_ALT,
            "error": "API geçersiz JSON yanıtı döndürdü!"
        }), 500

# 2. TC Sorgu
@app.route('/Api/tc.php')
def tc_api():
    tc = request.args.get('tc', '')
    
    if not tc:
        return jsonify({
            "info": INFO_TELEGRAM,
            "error": "Lütfen ?tc= parametresi girin!"
        }), 400
    
    if not validate_tc(tc):
        return jsonify({
            "info": INFO_TELEGRAM,
            "error": "Geçersiz TC kimlik numarası!"
        }), 400
    
    url = f"https://zyrdaware.xyz/api/tcpro?auth=t.me/zyrdaware&tc={tc}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
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
                }
            }
            return jsonify(output)
        else:
            return jsonify({
                "info": INFO_TELEGRAM,
                "error": "TC kimlik numarası bulunamadı!"
            }), 404
            
    except requests.RequestException as e:
        return jsonify({
            "info": INFO_TELEGRAM,
            "error": f"API bağlantı hatası: {str(e)}"
        }), 500
    except json.JSONDecodeError:
        return jsonify({
            "info": INFO_TELEGRAM,
            "error": "API geçersiz JSON yanıtı döndürdü!"
        }), 500

# 3. Aile Sorgu
@app.route('/Api/aile.php')
def aile_api():
    tc = request.args.get('tc', '')
    
    if not tc:
        return jsonify({
            "info": INFO_ALT,
            "error": "Lütfen ?tc= parametresi girin!"
        }), 400
    
    if not validate_tc(tc):
        return jsonify({
            "info": INFO_ALT,
            "error": "Geçersiz TC kimlik numarası!"
        }), 400
    
    url = f"https://zyrdaware.xyz/api/aile?auth=t.me/zyrdaware&tc={tc}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "veri" not in data or not isinstance(data["veri"], list):
            return jsonify({
                "info": "t.me/DemirKocs",
                "error": "API'den beklenen veri yapısı alınamadı!"
            }), 500
        
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
            "data": aile
        }
        
        return jsonify(output)
        
    except requests.RequestException as e:
        return jsonify({
            "info": INFO_ALT,
            "error": f"API bağlantı hatası: {str(e)}"
        }), 500
    except json.JSONDecodeError:
        return jsonify({
            "info": INFO_ALT,
            "error": "API geçersiz JSON yanıtı döndürdü!"
        }), 500

# 4. TC-GSM Sorgu
@app.route('/Api/tcgsm.php')
def tcgsm_api():
    tc = request.args.get('tc', '')
    
    if not tc:
        return jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": []
        }), 400
    
    if not validate_tc(tc):
        return jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": []
        }), 400
    
    if not rate_limit():
        return jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": []
        }), 429
    
    url = f"https://zyrdaware.xyz/api/tcgsm?auth=t.me/zyrdaware&tc={tc}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        veri = data.get("veri", [])
        
        return jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": veri
        })
        
    except requests.RequestException:
        return jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": []
        }), 500
    except json.JSONDecodeError:
        return jsonify({
            "info": "nerde beles oraya yerles dimi piiiccc",
            "veri": []
        }), 500

# 5. GSM-TC Sorgu
@app.route('/Api/gsmtc.php')
def gsmtc_api():
    gsm = request.args.get('gsm', '')
    
    if not gsm:
        return jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": []
        }), 400
    
    if not validate_gsm(gsm):
        return jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": []
        }), 400
    
    if not rate_limit():
        return jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": []
        }), 429
    
    url = f"https://zyrdaware.xyz/api/gsmtc?auth=t.me/zyrdaware&gsm={gsm}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        veri = []
        if "veri" in data and isinstance(data["veri"], list):
            for item in data["veri"]:
                veri.append({
                    "gsm": gsm,
                    "tc": item.get('tc') or item.get('TC') or item.get('Tc') or ''
                })
        
        return jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": veri
        })
        
    except requests.RequestException:
        return jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": []
        }), 500
    except json.JSONDecodeError:
        return jsonify({
            "info": "yarrak auth koydum bahdghysauagfcdsd",
            "veri": []
        }), 500

# 6. Adres Sorgu
@app.route('/Api/adres.php')
def adres_api():
    tc = request.args.get('tc', '')
    
    if not tc:
        return jsonify({
            "info": INFO_TELEGRAM,
            "error": "Lütfen ?tc= parametresi girin!"
        }), 400
    
    url = f"https://hold-periodically-file-oriented.trycloudflare.com/Api/adres.php?tc={tc}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # success anahtarını kaldır
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
            }
        }
        
        return jsonify(output)
        
    except requests.RequestException as e:
        return jsonify({
            "info": INFO_TELEGRAM,
            "error": f"API bağlantı hatası: {str(e)}"
        }), 500
    except json.JSONDecodeError:
        return jsonify({
            "info": INFO_TELEGRAM,
            "error": "API geçersiz JSON yanıtı döndürdü!"
        }), 500

# 7. Sülale Sorgu
@app.route('/Api/sulale.php')
def sulale_api():
    tc = request.args.get('tc', '')
    
    if not tc:
        return jsonify({
            "info": INFO_ALT,
            "error": "Lütfen ?tc= parametresi girin!"
        }), 400
    
    url = f"https://sorgusuz.world/api/s%C3%BClale.php?tc={tc}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "data" not in data or not isinstance(data["data"], list):
            return jsonify({
                "info": INFO_ALT,
                "error": "API'den beklenen veri yapısı alınamadı!"
            }), 500
        
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
            "yarramkadardata": sulale
        }
        
        return jsonify(output)
        
    except requests.RequestException as e:
        return jsonify({
            "info": INFO_ALT,
            "error": f"API bağlantı hatası: {str(e)}"
        }), 500
    except json.JSONDecodeError:
        return jsonify({
            "info": INFO_ALT,
            "error": "API geçersiz JSON yanıtı döndürdü!"
        }), 500

# 8. AdresNo Sorgu
@app.route('/Api/adresno.php')
def adresno_api():
    adresNo = request.args.get('adresNo', '')
    
    if not adresNo:
        return jsonify({
            'hata': 'Geçersiz adresNo. 10 haneli rakam olmalıdır.',
            'ornek': 'sıze ornek yok oclar fsffsfsmköslsxfsfsf'
        }), 400
    
    if not validate_adresno(adresNo):
        return jsonify({
            'hata': 'Geçersiz adresNo. 10 haneli rakam olmalıdır.',
            'ornek': 'sıze ornek yok oclar fsffsfsmköslsxfsfsf'
        }), 400
    
    url = f"https://dijital.gib.gov.tr/apigateway/api/nologin/mernis/adres-bilgisi-getir-with-adres-no?adresNo={adresNo}"
    
    try:
        headers = {
            "User-Agent": "GibAdresApi/1.0 (+https://senindomain.com)"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if "adresAciklama" in data:
            return jsonify({
                'basarili': True,
                'adresNo': adresNo,
                'tamAdres': data['adresAciklama'],
                'mahalle': data.get('mahAd'),
                'caddeSokak': data.get('csbmAd'),
                'disKapiNo': data.get('disKapiNo'),
                'icKapiNo': data.get('icKapiNo')
            })
        else:
            return jsonify({
                'basarili': False,
                'hata': 'Bu adresNo ile kayıtlı adres bulunamadı.'
            }), 404
            
    except requests.RequestException as e:
        return jsonify({
            'hata': f'GİB sunucusundan yanıt alınamadı: {str(e)}'
        }), 502
    except json.JSONDecodeError:
        return jsonify({
            'hata': 'GİB yanıtını ayrıştıramadı (JSON hatası).'
        }), 502

# 9. IP Sorgu
@app.route('/Api/ip.php')
def ip_api():
    ip = request.args.get('ip', '')
    
    # Eğer IP verilmediyse, kullanıcının IP'sini al
    if not ip:
        ip = request.remote_addr
        
        # Proxy kontrolü
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('HTTP_CF_CONNECTING_IP'):
            ip = request.headers.get('HTTP_CF_CONNECTING_IP')
    
    if not validate_ip(ip):
        return jsonify({
            'status': 'error',
            'message': 'Geçersiz IP adresi formatı',
            'info': INFO_TELEGRAM,
            'received_ip': ip
        }), 400
    
    # Farklı API servisleri
    apis = {
        'ipapi': f"https://ipapi.co/{ip}/json/",
        'ipinfo': f"https://ipinfo.io/{ip}/json",
        'ipapi_com': f"http://ip-api.com/json/{ip}"
    }
    
    results = {}
    for service, url in apis.items():
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (IP Sorgu API - t.me/DemirKocs)"
            }
            response = requests.get(url, headers=headers, timeout=10)
            results[service] = {
                'data': response.json() if response.status_code == 200 else None,
                'http_code': response.status_code,
                'service': service
            }
        except:
            results[service] = {
                'data': None,
                'http_code': 500,
                'service': service
            }
    
    # Başarılı bir yanıt bul
    final_data = None
    used_service = None
    
    for service, result in results.items():
        if result['http_code'] == 200 and result['data']:
            final_data = result['data']
            used_service = service
            break
    
    if final_data:
        # Standart format oluştur
        standardized_data = {
            'info': INFO_TELEGRAM,
            'status': 'success',
            'query': ip,
            'data': {}
        }
        
        # API'ye göre veriyi işle
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
        
        return jsonify(standardized_data)
    else:
        # Tüm API'ler başarısız oldu
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
            'api_status': {
                service: results[service]['http_code'] for service in results
            }
        }
        return jsonify(response), 502

# 10. Aile Sorgu (çocuklar)
@app.route('/Apiaile.php')
def aile_cocuk_api():
    tc = request.args.get('tc', '')
    
    if not tc:
        return jsonify({
            'status': 'error',
            'message': 'TC kimlik numarası gerekli',
            'usage': '?tc=11111111110'
        }), 400
    
    if not validate_tc(tc):
        return jsonify({
            'status': 'error',
            'message': 'Geçersiz TC kimlik numarası formatı (11 rakam olmalı)'
        }), 400
    
    url = f'https://hold-periodically-file-oriented.trycloudflare.com/Api/cocuk.php?tc={tc}'
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        return jsonify(response.json()), response.status_code
        
    except requests.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': 'API bağlantı hatası',
            'error': str(e)
        }), 500

# 11. İşyeri Sorgu
@app.route('/Mernis/Api/isyeri.php')
def isyeri_api():
    tc = request.args.get('tc', '')
    
    if not tc:
        return jsonify({
            'status': False,
            'message': 'TC kimlik numarası gerekli',
            'example': '?tc=15689993550'
        }), 400
    
    if not validate_tc(tc):
        return jsonify({
            'status': False,
            'message': 'Geçersiz TC kimlik numarası formatı (11 rakam olmalı)'
        }), 400
    
    url = f'https://hold-periodically-file-oriented.trycloudflare.com/Mernis/Api/isyeri.php?tc={tc}'
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        try:
            data = response.json()
            return jsonify(data), response.status_code
        except json.JSONDecodeError:
            return jsonify({
                'status': False,
                'message': 'API geçersiz JSON yanıtı döndürdü',
                'raw_response': response.text[:500]
            }), 502
            
    except requests.RequestException as e:
        return jsonify({
            'status': False,
            'message': 'API bağlantı hatası',
            'error': str(e)
        }), 500

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
    <title>CROOS Checker | API</title>
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

        /* Galaksi Efekti Konteyneri */
        .space {
            position: fixed;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: 0;
            overflow: hidden;
        }

        /* Yıldızlar */
        .star {
            position: absolute;
            width: 2px;
            height: 2px;
            background: white;
            border-radius: 50%;
            animation: moveStar linear infinite;
        }

        /* Yıldız Hareketi Animasyonu */
        @keyframes moveStar {
            0% { transform: translateY(0) translateX(0); opacity: 1; }
            100% { transform: translateY(100vh) translateX(-100vw); opacity: 0; }
        }

        /* Kayan Yıldızlar */
        .shooting-star {
            position: absolute;
            color: white;
            font-size: 10px;
            opacity: 0.9;
            transform: rotate(45deg);
            text-shadow: -5px -5px 0 rgba(255,255,255,0.2), -10px -10px 0 rgba(255,255,255,0.1);
            animation: shootStar 2s linear;
        }

        /* Kayan Yıldız Animasyonu */
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

        .info-section h3 i {
            color: var(--accent-color);
            text-shadow: 0 0 5px rgba(255, 255, 255, 0.7);
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

        /* MOBİL UYUMLULUK */
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
    <!-- Galaksi Efekti İçin Konteyner -->
    <div class="space" id="space"></div>

    <div class="container">
        <div class="header">
            <h1>CROOS CHECKER</h1>
            <p class="subtitle">Profesyonel Sorgu API Servisleri</p>
        </div>

        <div class="api-container">
            <div class="api-card">
                <h3><i class="fas fa-user"></i> Ad Soyad Sorgu</h3>
                <div class="api-url" id="api-url-1">http://localhost:5000/Api/adsoyad.php?ad=roket&soyad=atar&il=&ilce=</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Api/adsoyad.php?ad=roket&soyad=atar&il=&ilce=" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Api/adsoyad.php?ad=roket&soyad=atar&il=&ilce=')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-id-card"></i> TC Sorgu</h3>
                <div class="api-url" id="api-url-2">http://localhost:5000/Api/tc.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Api/tc.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Api/tc.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-users"></i> Aile Sorgu</h3>
                <div class="api-url" id="api-url-3">http://localhost:5000/Api/aile.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Api/aile.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Api/aile.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-phone"></i> TC-GSM Sorgu</h3>
                <div class="api-url" id="api-url-4">http://localhost:5000/Api/tcgsm.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Api/tcgsm.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Api/tcgsm.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-phone-alt"></i> GSM-TC Sorgu</h3>
                <div class="api-url" id="api-url-5">http://localhost:5000/Api/gsmtc.php?gsm=5415722525</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Api/gsmtc.php?gsm=5415722525" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Api/gsmtc.php?gsm=5415722525')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-map-marker-alt"></i> Adres Sorgu</h3>
                <div class="api-url" id="api-url-6">http://localhost:5000/Api/adres.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Api/adres.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Api/adres.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-family"></i> Sülale Sorgu</h3>
                <div class="api-url" id="api-url-7">http://localhost:5000/Api/sulale.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Api/sulale.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Api/sulale.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-home"></i> Adresno Sorgu</h3>
                <div class="api-url" id="api-url-8">http://localhost:5000/Api/adresno.php?adresNo=3212827459</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Api/adresno.php?adresNo=3212827459" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Api/adresno.php?adresNo=3212827459')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-network-wired"></i> IP Sorgu</h3>
                <div class="api-url" id="api-url-9">http://localhost:5000/Api/ip.php?ip=8.8.8.8</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Api/ip.php?ip=8.8.8.8" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Api/ip.php?ip=8.8.8.8')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-baby"></i> Çocuk Sorgu</h3>
                <div class="api-url" id="api-url-10">http://localhost:5000/Apiaile.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Apiaile.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Apiaile.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-building"></i> İşyeri Sorgu</h3>
                <div class="api-url" id="api-url-11">http://localhost:5000/Mernis/Api/isyeri.php?tc=11111111110</div>
                <div class="button-group">
                    <a href="http://localhost:5000/Mernis/Api/isyeri.php?tc=11111111110" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> Git
                    </a>
                    <button onclick="copyLink(this, 'http://localhost:5000/Mernis/Api/isyeri.php?tc=11111111110')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>
        </div>

        <div class="info-section">
            <h3><i class="fas fa-info-circle"></i> Bilgilendirme</h3>
            <p>Tüm API'ler ücretsiz olarak sunulmaktadır. API'ler sadece eğitim amaçlıdır. Kötüye kullanım durumunda erişim engellenebilir.</p>
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
            </div>
        </div>
    </div>

    <script>
        // Galaksi efekti için JavaScript
        const space = document.getElementById('space');

        // Yıldızları oluşturma
        for(let i=0; i<120; i++){
            const star = document.createElement('div');
            star.className = 'star';
            star.style.top = Math.random()*100+'%';
            star.style.left = Math.random()*100+'%';
            star.style.animationDuration = (Math.random()*5+5)+'s';
            space.appendChild(star);
        }

        // Kayan yıldızları oluşturma
        setInterval(()=>{
            const shooting = document.createElement('div');
            shooting.className = 'shooting-star';
            shooting.innerHTML = '✦';
            shooting.style.top = Math.random()*50+'%';
            shooting.style.left = Math.random()*50+'%';
            space.appendChild(shooting);
            setTimeout(()=>shooting.remove(), 2500);
        }, 4000);

        // Link kopyalama fonksiyonu
        async function copyLink(button, textToCopy) {
            try {
                await navigator.clipboard.writeText(textToCopy);
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

        // URL'leri dinamik olarak güncelle (localhost yerine sunucu adresi)
        document.addEventListener('DOMContentLoaded', function() {
            const baseUrl = window.location.origin; // http://localhost:5000 veya domain
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

                // Butonların href'lerini de güncelle
                const button = element?.closest('.api-card')?.querySelector('.btn-primary');
                if (button) {
                    button.href = baseUrl + api.url;
                }

                // Kopyala butonlarını da güncelle
                const copyButtons = document.querySelectorAll('.btn-secondary');
                copyButtons.forEach((btn, index) => {
                    if (index < apiUrls.length) {
                        btn.onclick = function() {
                            copyLink(this, baseUrl + apiUrls[index].url);
                        };
                    }
                });
            });
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
