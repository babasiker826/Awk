from flask import Flask, request, jsonify
import requests
import logging
import re

# Logging ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# TEK ANAHTAR - HERKESE AÇIK
MASTER_API_KEY = "nabibabadir"

# Tüm upstream API'ler
UPSTREAM_APIS = {
    # 4040 portundaki API'ler
    "adsoyad": "http://45.81.113.22:4040/adsoyad",
    "tc": "http://45.81.113.22:4040/tc",
    "aile": "http://45.81.113.22:4040/aile",
    "cocuk": "http://45.81.113.22:4040/cocuk",
    "anne": "http://45.81.113.22:4040/anne",
    "baba": "http://45.81.113.22:4040/baba",
    
    # 4000 portundaki API'ler
    "adres": "http://45.81.113.22:4000/f3system/api/adres",
    "hane": "http://45.81.113.22:4000/f3system/api/hane",
    "sulale": "http://45.81.113.22:4000/f3system/api/sulale",
    
    # Diğer external API'ler
    "plaka_adsoyad": "https://plakaf3.onrender.com/f3/api/adsoyadplaka",
    "papara_no": "https://paparadata.onrender.com/f3system/api/papara",
    "papara_adsoyad": "https://paparadata.onrender.com/f3system/api/papara",
    "eczane": "https://eczanedataf3.onrender.com/f3system/api/eczane",
    "serino": "https://serinodataf3.onrender.com/serino",
    "plaka": "https://plaka-uqg8.onrender.com/f3api/plaka"
}

# Basit API Key kontrolü
def require_api_key(f):
    def wrapper(*args, **kwargs):
        api_key = request.args.get('key')
        
        if api_key != MASTER_API_KEY:
            return jsonify({
                "error": True,
                "message": "Geçersiz API Key! Doğru key: nabibabadir",
                "usage": "Tüm sorgularda ?key=nabibabadir parametresini ekleyin"
            }), 401
        
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# TC Kimlik doğrulama
def validate_tc(tc):
    if not tc or not tc.isdigit() or len(tc) != 11:
        return False
    return True

# Input sanitization
def sanitize_input(input_str):
    if not input_str:
        return ""
    return re.sub(r'[^a-zA-Z0-9ğüşıöçĞÜŞİÖÇ\s\-\.]', '', input_str)

# ============ API ENDPOINT'LERİ ============

# 1. Ad Soyad Sorgu
@app.route('/Api/adsoyad.php', methods=['GET'])
@require_api_key
def api_adsoyad():
    ad = request.args.get('ad', '')
    soyad = request.args.get('soyad', '')
    il = request.args.get('il', '')
    ilce = request.args.get('ilce', '')
    
    if not ad or not soyad:
        return jsonify({
            "error": True,
            "message": "Ad ve soyad gereklidir",
            "example": "/Api/adsoyad.php?ad=ALİ&soyad=YILMAZ&key=nabibabadir"
        }), 400
    
    try:
        results = {"ad": ad, "soyad": soyad, "data": {}}
        
        # Ad Soyad sorgusu
        try:
            params = f"?ad={ad}&soyad={soyad}"
            if il:
                params += f"&il={il}"
            if ilce:
                params += f"&ilce={ilce}"
                
            response = requests.get(
                f"{UPSTREAM_APIS['adsoyad']}{params}",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["kisi_bilgileri"] = response.json()
        except Exception as e:
            logger.error(f"Ad soyad sorgu hatası: {str(e)}")
        
        # Plaka sorgusu (ad soyad ile)
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['plaka_adsoyad']}?ad={ad}&soyad={soyad}",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["plaka_bilgileri"] = response.json()
        except:
            pass
        
        # Papara sorgusu (ad soyad ile)
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['papara_adsoyad']}?ad={ad}&soyad={soyad}",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["papara_bilgileri"] = response.json()
        except:
            pass
        
        return jsonify({
            "success": True,
            "query": {"ad": ad, "soyad": soyad, "il": il, "ilce": ilce},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 2. TC Sorgu
@app.route('/Api/tc.php', methods=['GET'])
@require_api_key
def api_tc():
    tc = request.args.get('tc', '')
    
    if not validate_tc(tc):
        return jsonify({
            "error": True,
            "message": "Geçersiz TC kimlik numarası",
            "example": "/Api/tc.php?tc=11111111110&key=nabibabadir"
        }), 400
    
    try:
        results = {"tc": tc, "data": {}}
        
        # TC sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['tc']}?tc={tc}",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["kisi_bilgileri"] = response.json()
        except Exception as e:
            logger.error(f"TC sorgu hatası: {str(e)}")
        
        # Adres sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['adres']}?tc={tc}&key=F3-TEST-KEY-123",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["adres_bilgileri"] = response.json()
        except:
            pass
        
        # Hane sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['hane']}?tc={tc}&key=F3-TEST-KEY-123",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["hane_bilgileri"] = response.json()
        except:
            pass
        
        return jsonify({
            "success": True,
            "query": {"tc": tc},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 3. Aile Sorgu
@app.route('/Api/aile.php', methods=['GET'])
@require_api_key
def api_aile():
    tc = request.args.get('tc', '')
    
    if not validate_tc(tc):
        return jsonify({
            "error": True,
            "message": "Geçersiz TC kimlik numarası",
            "example": "/Api/aile.php?tc=11111111110&key=nabibabadir"
        }), 400
    
    try:
        results = {"tc": tc, "data": {}}
        
        # Aile sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['aile']}?tc={tc}",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["aile_bilgileri"] = response.json()
        except Exception as e:
            logger.error(f"Aile sorgu hatası: {str(e)}")
        
        # Sülale sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['sulale']}?tc={tc}&key=F3-TEST-KEY-123",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["sulale_bilgileri"] = response.json()
        except:
            pass
        
        return jsonify({
            "success": True,
            "query": {"tc": tc},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 4. TC-GSM Sorgu
@app.route('/Api/tcgsm.php', methods=['GET'])
@require_api_key
def api_tcgsm():
    tc = request.args.get('tc', '')
    
    if not validate_tc(tc):
        return jsonify({
            "error": True,
            "message": "Geçersiz TC kimlik numarası",
            "example": "/Api/tcgsm.php?tc=11111111110&key=nabibabadir"
        }), 400
    
    try:
        results = {"tc": tc, "data": {}}
        
        # TC sorgusu (telefon bilgilerini al)
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['tc']}?tc={tc}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                # Telefon bilgilerini çıkar
                gsm_info = {}
                if isinstance(data, dict):
                    for key, value in data.items():
                        if 'telefon' in key.lower() or 'gsm' in key.lower() or 'cep' in key.lower():
                            gsm_info[key] = value
                
                results["data"]["gsm_bilgileri"] = gsm_info if gsm_info else data
        except Exception as e:
            logger.error(f"TC-GSM sorgu hatası: {str(e)}")
        
        return jsonify({
            "success": True,
            "query": {"tc": tc},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 5. GSM-TC Sorgu
@app.route('/Api/gsmtc.php', methods=['GET'])
@require_api_key
def api_gsmtc():
    gsm = request.args.get('gsm', '')
    
    if not gsm or not gsm.isdigit() or len(gsm) < 10:
        return jsonify({
            "error": True,
            "message": "Geçerli GSM numarası giriniz",
            "example": "/Api/gsmtc.php?gsm=5415722525&key=nabibabadir"
        }), 400
    
    try:
        results = {"gsm": gsm, "data": {}}
        
        # Bu endpoint için mevcut bir API yok, bilgi mesajı döndür
        results["data"]["message"] = "GSM-TC sorgusu şu an kullanılamıyor"
        results["data"]["gsm"] = gsm
        
        return jsonify({
            "success": True,
            "query": {"gsm": gsm},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 6. Adres Sorgu
@app.route('/Api/adres.php', methods=['GET'])
@require_api_key
def api_adres():
    tc = request.args.get('tc', '')
    
    if not validate_tc(tc):
        return jsonify({
            "error": True,
            "message": "Geçersiz TC kimlik numarası",
            "example": "/Api/adres.php?tc=11111111110&key=nabibabadir"
        }), 400
    
    try:
        results = {"tc": tc, "data": {}}
        
        # Adres sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['adres']}?tc={tc}&key=F3-TEST-KEY-123",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["adres_bilgileri"] = response.json()
        except Exception as e:
            logger.error(f"Adres sorgu hatası: {str(e)}")
        
        # Hane sorgusu (adres ile ilgili)
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['hane']}?tc={tc}&key=F3-TEST-KEY-123",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["hane_bilgileri"] = response.json()
        except:
            pass
        
        return jsonify({
            "success": True,
            "query": {"tc": tc},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 7. Sülale Sorgu
@app.route('/Api/sulale.php', methods=['GET'])
@require_api_key
def api_sulale():
    tc = request.args.get('tc', '')
    
    if not validate_tc(tc):
        return jsonify({
            "error": True,
            "message": "Geçersiz TC kimlik numarası",
            "example": "/Api/sulale.php?tc=11111111110&key=nabibabadir"
        }), 400
    
    try:
        results = {"tc": tc, "data": {}}
        
        # Sülale sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['sulale']}?tc={tc}&key=F3-TEST-KEY-123",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["sulale_bilgileri"] = response.json()
        except Exception as e:
            logger.error(f"Sülale sorgu hatası: {str(e)}")
        
        return jsonify({
            "success": True,
            "query": {"tc": tc},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 8. Adresno Sorgu
@app.route('/Api/adresno.php', methods=['GET'])
@require_api_key
def api_adresno():
    adresNo = request.args.get('adresNo', '')
    
    if not adresNo or not adresNo.isdigit():
        return jsonify({
            "error": True,
            "message": "Geçerli adres numarası giriniz",
            "example": "/Api/adresno.php?adresNo=3212827459&key=nabibabadir"
        }), 400
    
    try:
        results = {"adresNo": adresNo, "data": {}}
        
        # Adresno için mevcut API yok, bilgi mesajı
        results["data"]["message"] = "AdresNo sorgusu şu an kullanılamıyor"
        results["data"]["adres_no"] = adresNo
        
        return jsonify({
            "success": True,
            "query": {"adresNo": adresNo},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 9. IP Sorgu
@app.route('/Api/ip.php', methods=['GET'])
@require_api_key
def api_ip():
    ip = request.args.get('ip', '')
    
    if not ip:
        # Eğer IP belirtilmemişse, isteğin geldiği IP'yi al
        ip = request.remote_addr
    
    try:
        results = {"ip": ip, "data": {}}
        
        # IP sorgusu için basit bir yanıt
        results["data"]["ip_address"] = ip
        results["data"]["query_time"] = datetime.now().isoformat()
        results["data"]["service"] = "f3system IP Lookup"
        
        # IP geolocation için ücretsiz API (opsiyonel)
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            if response.status_code == 200:
                geo_data = response.json()
                if geo_data.get("status") == "success":
                    results["data"]["geolocation"] = {
                        "country": geo_data.get("country"),
                        "city": geo_data.get("city"),
                        "isp": geo_data.get("isp"),
                        "lat": geo_data.get("lat"),
                        "lon": geo_data.get("lon")
                    }
        except:
            pass
        
        return jsonify({
            "success": True,
            "query": {"ip": ip},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 10. Çocuk Sorgu
@app.route('/Api/ailecocuk.php', methods=['GET'])
@require_api_key
def api_ailecocuk():
    tc = request.args.get('tc', '')
    
    if not validate_tc(tc):
        return jsonify({
            "error": True,
            "message": "Geçersiz TC kimlik numarası",
            "example": "/Api/ailecocuk.php?tc=11111111110&key=nabibabadir"
        }), 400
    
    try:
        results = {"tc": tc, "data": {}}
        
        # Çocuk sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['cocuk']}?tc={tc}",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["cocuk_bilgileri"] = response.json()
        except Exception as e:
            logger.error(f"Çocuk sorgu hatası: {str(e)}")
        
        return jsonify({
            "success": True,
            "query": {"tc": tc},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 11. İşyeri Sorgu
@app.route('/Api/isyeri.php', methods=['GET'])
@require_api_key
def api_isyeri():
    tc = request.args.get('tc', '')
    
    if not validate_tc(tc):
        return jsonify({
            "error": True,
            "message": "Geçersiz TC kimlik numarası",
            "example": "/Api/isyeri.php?tc=11111111110&key=nabibabadir"
        }), 400
    
    try:
        results = {"tc": tc, "data": {}}
        
        # İşyeri sorgusu için mevcut API yok
        results["data"]["message"] = "İşyeri sorgusu şu an kullanılamıyor"
        results["data"]["tc"] = tc
        
        return jsonify({
            "success": True,
            "query": {"tc": tc},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 12. Anne Sorgu
@app.route('/Api/anne.php', methods=['GET'])
@require_api_key
def api_anne():
    tc = request.args.get('tc', '')
    
    if not validate_tc(tc):
        return jsonify({
            "error": True,
            "message": "Geçersiz TC kimlik numarası",
            "example": "/Api/anne.php?tc=11111111110&key=nabibabadir"
        }), 400
    
    try:
        results = {"tc": tc, "data": {}}
        
        # Anne sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['anne']}?tc={tc}",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["anne_bilgileri"] = response.json()
        except Exception as e:
            logger.error(f"Anne sorgu hatası: {str(e)}")
        
        return jsonify({
            "success": True,
            "query": {"tc": tc},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# 13. Baba Sorgu
@app.route('/Api/baba.php', methods=['GET'])
@require_api_key
def api_baba():
    tc = request.args.get('tc', '')
    
    if not validate_tc(tc):
        return jsonify({
            "error": True,
            "message": "Geçersiz TC kimlik numarası",
            "example": "/Api/baba.php?tc=11111111110&key=nabibabadir"
        }), 400
    
    try:
        results = {"tc": tc, "data": {}}
        
        # Baba sorgusu
        try:
            response = requests.get(
                f"{UPSTREAM_APIS['baba']}?tc={tc}",
                timeout=10
            )
            if response.status_code == 200:
                results["data"]["baba_bilgileri"] = response.json()
        except Exception as e:
            logger.error(f"Baba sorgu hatası: {str(e)}")
        
        return jsonify({
            "success": True,
            "query": {"tc": tc},
            "results": results["data"]
        })
        
    except Exception as e:
        logger.error(f"API hatası: {str(e)}")
        return jsonify({
            "error": True,
            "message": "Sorgu sırasında hata oluştu"
        }), 500

# ============ DASHBOARD ============
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

        .api-key-box {
            background: rgba(76, 175, 80, 0.1);
            border: 2px solid var(--primary-color);
            padding: 15px;
            border-radius: 10px;
            margin: 20px auto;
            max-width: 600px;
            text-align: center;
        }

        .api-key {
            font-family: monospace;
            font-size: 1.5rem;
            color: var(--primary-color);
            font-weight: bold;
            margin: 10px 0;
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
            
            <div class="api-key-box">
                <p style="margin-bottom: 10px; color: #4CAF50; font-weight: bold;">TEK ANAHTAR - HERKESE AÇIK</p>
                <div class="api-key">?key=nabibabadir</div>
                <p style="margin-top: 10px; font-size: 0.9rem; color: #aaa;">Tüm API sorgularında bu anahtarı kullanın</p>
            </div>
            
            <div class="api-status">
                <span class="status-indicator status-online"></span>
                <span>Tüm API'ler Aktif | Ücretsiz Kullanım | 13 Farklı Sorgu</span>
            </div>
        </div>

        <div class="api-container">
            <div class="api-card">
                <h3><i class="fas fa-user"></i> Ad Soyad Sorgu</h3>
                <div class="api-url" id="api-url-1">/Api/adsoyad.php?ad=ALİ&soyad=YILMAZ&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/adsoyad.php?ad=ALİ&soyad=YILMAZ&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/adsoyad.php?ad=ALİ&soyad=YILMAZ&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-id-card"></i> TC Sorgu</h3>
                <div class="api-url" id="api-url-2">/Api/tc.php?tc=11111111110&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/tc.php?tc=11111111110&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/tc.php?tc=11111111110&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-users"></i> Aile Sorgu</h3>
                <div class="api-url" id="api-url-3">/Api/aile.php?tc=11111111110&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/aile.php?tc=11111111110&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/aile.php?tc=11111111110&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-phone"></i> TC-GSM Sorgu</h3>
                <div class="api-url" id="api-url-4">/Api/tcgsm.php?tc=11111111110&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/tcgsm.php?tc=11111111110&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/tcgsm.php?tc=11111111110&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-phone-alt"></i> GSM-TC Sorgu</h3>
                <div class="api-url" id="api-url-5">/Api/gsmtc.php?gsm=5415722525&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/gsmtc.php?gsm=5415722525&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/gsmtc.php?gsm=5415722525&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-map-marker-alt"></i> Adres Sorgu</h3>
                <div class="api-url" id="api-url-6">/Api/adres.php?tc=11111111110&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/adres.php?tc=11111111110&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/adres.php?tc=11111111110&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-family"></i> Sülale Sorgu</h3>
                <div class="api-url" id="api-url-7">/Api/sulale.php?tc=11111111110&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/sulale.php?tc=11111111110&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/sulale.php?tc=11111111110&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-home"></i> Adresno Sorgu</h3>
                <div class="api-url" id="api-url-8">/Api/adresno.php?adresNo=3212827459&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/adresno.php?adresNo=3212827459&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/adresno.php?adresNo=3212827459&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-network-wired"></i> IP Sorgu</h3>
                <div class="api-url" id="api-url-9">/Api/ip.php?ip=8.8.8.8&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/ip.php?ip=8.8.8.8&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/ip.php?ip=8.8.8.8&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-baby"></i> Çocuk Sorgu</h3>
                <div class="api-url" id="api-url-10">/Api/ailecocuk.php?tc=11111111110&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/ailecocuk.php?tc=11111111110&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/ailecocuk.php?tc=11111111110&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-building"></i> İşyeri Sorgu</h3>
                <div class="api-url" id="api-url-11">/Api/isyeri.php?tc=11111111110&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/isyeri.php?tc=11111111110&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/isyeri.php?tc=11111111110&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-female"></i> Anne Sorgu</h3>
                <div class="api-url" id="api-url-12">/Api/anne.php?tc=11111111110&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/anne.php?tc=11111111110&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/anne.php?tc=11111111110&key=nabibabadir')" class="btn btn-secondary">
                        <i class="far fa-copy"></i> Kopyala
                    </button>
                </div>
            </div>

            <div class="api-card">
                <h3><i class="fas fa-male"></i> Baba Sorgu</h3>
                <div class="api-url" id="api-url-13">/Api/baba.php?tc=11111111110&key=nabibabadir</div>
                <div class="button-group">
                    <a href="/Api/baba.php?tc=11111111110&key=nabibabadir" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt"></i> API'yi Aç
                    </a>
                    <button onclick="copyLink(this, '/Api/baba.php?tc=11111111110&key=nabibabadir')" class="btn btn-secondary">
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
            <p><strong>API Key:</strong> Tüm sorgularda <code>?key=nabibabadir</code> parametresini ekleyin</p>
            <p><strong>Format:</strong> JSON</p>
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
                {id: 'api-url-1', url: '/Api/adsoyad.php?ad=eymen&soyad=yavuz&key=nabibabadir'},
                {id: 'api-url-2', url: '/Api/tc.php?tc=11111111110&key=nabibabadir'},
                {id: 'api-url-3', url: '/Api/aile.php?tc=11111111110&key=nabibabadir'},
                {id: 'api-url-4', url: '/Api/tcgsm.php?tc=11111111110&key=nabibabadir'},
                {id: 'api-url-5', url: '/Api/gsmtc.php?gsm=5415722525&key=nabibabadir'},
                {id: 'api-url-6', url: '/Api/adres.php?tc=11111111110&key=nabibabadir'},
                {id: 'api-url-7', url: '/Api/sulale.php?tc=11111111110&key=nabibabadir'},
                {id: 'api-url-8', url: '/Api/adresno.php?adresNo=3212827459&key=nabibabadir'},
                {id: 'api-url-9', url: '/Api/ip.php?ip=8.8.8.8&key=nabibabadir'},
                {id: 'api-url-10', url: '/Api/ailecocuk.php?tc=11111111110&key=nabibabadir'},
                {id: 'api-url-11', url: '/Api/isyeri.php?tc=11111111110&key=nabibabadir'},
                {id: 'api-url-12', url: '/Api/anne.php?tc=11111111110&key=nabibabadir'},
                {id: 'api-url-13', url: '/Api/baba.php?tc=11111111110&key=nabibabadir'}
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
        
        .api-key-box {
            background: rgba(76, 175, 80, 0.1);
            border: 2px solid #4CAF50;
            padding: 20px;
            border-radius: 10px;
            margin: 30px auto;
            max-width: 500px;
        }
        
        .api-key {
            font-family: monospace;
            font-size: 2rem;
            color: #4CAF50;
            font-weight: bold;
            margin: 10px 0;
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
        
        <div class="api-key-box">
            <p style="color: #aaa; margin-bottom: 10px;">TEK ANAHTAR - HERKESE AÇIK</p>
            <div class="api-key">?key=nabibabadir</div>
            <p style="color: #aaa; margin-top: 10px; font-size: 0.9rem;">
                Tüm sorgularda bu anahtarı kullanın
            </p>
        </div>
        
        <div class="description">
            <p>13 farklı sorgu API'si ile kişi, aile, adres, IP ve işyeri bilgilerine hızlı ve güvenli erişim.</p>
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
                <span class="stat-number">13</span>
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

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "f3system API Gateway",
        "version": "2.0",
        "api_key": "nabibabadir",
        "total_endpoints": 13,
        "endpoints": [
            "/Api/adsoyad.php?ad=eymen&soyad=yavuz&key=nabibabadir",
            "/Api/tc.php?tc=11111111110&key=nabibabadir",
            "/Api/aile.php?tc=11111111110&key=nabibabadir",
            "/Api/tcgsm.php?tc=11111111110&key=nabibabadir",
            "/Api/gsmtc.php?gsm=5415722525&key=nabibabadir",
            "/Api/adres.php?tc=11111111110&key=nabibabadir",
            "/Api/sulale.php?tc=11111111110&key=nabibabadir",
            "/Api/adresno.php?adresNo=3212827459&key=nabibabadir",
            "/Api/ip.php?ip=8.8.8.8&key=nabibabadir",
            "/Api/ailecocuk.php?tc=11111111110&key=nabibabadir",
            "/Api/isyeri.php?tc=11111111110&key=nabibabadir",
            "/Api/anne.php?tc=11111111110&key=nabibabadir",
            "/Api/baba.php?tc=11111111110&key=nabibabadir"
        ]
    })

if __name__ == '__main__':
    print("""
    ============================================
    f3system API Gateway Başlatılıyor...
    ============================================
    
    🚀 API Anahtar: nabibabadir
    📊 Toplam Endpoint: 13
    
    🌐 Ana Sayfa: /
    📱 API Dashboard: /Api
    ❤️  Health Check: /health
    
    🔑 Tüm sorgularda ?key=nabibabadir parametresi gereklidir!
    
    ============================================
    """)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
)
