# Crypto AI Trader

Professional cryptocurrency trading signals platform with AI-powered technical analysis.

## 🚀 Hızlı Kurulum (VPS'inize)

### 1. VPS'inize Bağlanın
```bash
ssh root@YOUR_VPS_IP
```

### 2. Projeyi İndirin
```bash
# Bu dosyaları VPS'inize yükleyin (SCP, SFTP veya manuel olarak)
# Alternatif: Git clone kullanabilirsiniz
```

### 3. Tek Komutla Kurulum
```bash
chmod +x deploy.sh
./deploy.sh
```

Bu komut:
- ✅ Docker'ı kurar
- ✅ Container'ı build eder
- ✅ Sistemi başlatır
- ✅ 7/24 çalışır hale getirir

## 📊 API Endpoints

### Sinyal Yönetimi
- `GET /api/signals` - Aktif sinyalleri listele
- `GET /api/signals/history` - Sinyal geçmişini listele
- `POST /api/signals/generate` - Manuel sinyal üret
- `POST /api/signals/update-prices` - Fiyatları güncelle

### Otomatik Tarama
- `POST /api/auto-scan/start` - Otomatik taramayı başlat
- `POST /api/auto-scan/stop` - Otomatik taramayı durdur
- `GET /api/auto-scan/status` - Tarama durumunu kontrol et

### Coin Verileri
- `GET /api/coins` - Tüm coinleri listele
- `GET /api/coins/filtered` - Filtrelenmiş coinleri listele

### Sistem
- `GET /api/health` - Sistem sağlığını kontrol et

## 🔧 Yönetim Komutları

### Container Yönetimi
```bash
# Container durumunu kontrol et
docker-compose ps

# Logları görüntüle
docker-compose logs -f

# Container'ı yeniden başlat
docker-compose restart

# Container'ı durdur
docker-compose down

# Container'ı başlat
docker-compose up -d
```

### Otomatik Tarama Kontrolü
```bash
# Otomatik taramayı başlat
curl -X POST http://localhost:5000/api/auto-scan/start

# Otomatik taramayı durdur
curl -X POST http://localhost:5000/api/auto-scan/stop

# Tarama durumunu kontrol et
curl http://localhost:5000/api/auto-scan/status
```

## 🎯 Özellikler

### 7/24 Otomatik Çalışma
- ✅ **Her 5 dakikada** otomatik tarama
- ✅ **Stablecoin filtreleme** (USDT, USDC, vb. hariç)
- ✅ **Volatilite kontrolü** (min %0.5)
- ✅ **Market cap filtreleme** ($10M - $100B)
- ✅ **Volume kontrolü** (min $1M)

### Akıllı Sinyal Üretimi
- ✅ **RSI analizi**
- ✅ **MACD sinyalleri**
- ✅ **Trend analizi**
- ✅ **Volume analizi**
- ✅ **Otomatik TP/SL hesaplama**

### Gerçek Zamanlı Takip
- ✅ **Fiyat güncellemeleri**
- ✅ **PnL hesaplama**
- ✅ **Otomatik sinyal kapatma**
- ✅ **Sinyal geçmişi**

## 🌐 Web Arayüzü

Sistem kurulduktan sonra web arayüzüne erişebilirsiniz:
```
http://YOUR_VPS_IP:5000
```

## 📱 Sistem Durumu

### Health Check
```bash
curl http://YOUR_VPS_IP:5000/api/health
```

### Aktif Sinyaller
```bash
curl http://YOUR_VPS_IP:5000/api/signals
```

## 🔒 Güvenlik

- Container izole çalışır
- Sadece gerekli portlar açık (5000)
- Otomatik restart özelliği
- Health check ile sürekli kontrol

## 📈 Performans

- **RAM kullanımı:** ~200MB
- **CPU kullanımı:** Düşük
- **Disk kullanımı:** ~500MB
- **Network:** API çağrıları için internet gerekli

## 🆘 Sorun Giderme

### Container Çalışmıyor
```bash
docker-compose logs
docker-compose restart
```

### API Erişim Sorunu
```bash
# Port kontrolü
netstat -tlnp | grep 5000

# Firewall kontrolü
ufw status
```

### Otomatik Tarama Çalışmıyor
```bash
# Tarama durumunu kontrol et
curl http://localhost:5000/api/auto-scan/status

# Manuel başlat
curl -X POST http://localhost:5000/api/auto-scan/start
```

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. `docker-compose logs` ile logları kontrol edin
2. `curl http://localhost:5000/api/health` ile sistem durumunu kontrol edin
3. Container'ı yeniden başlatın: `docker-compose restart`

## 🎉 Başarılı Kurulum Sonrası

Sistem başarıyla kurulduktan sonra:

1. **Otomatik taramayı başlatın:**
   ```bash
   curl -X POST http://YOUR_VPS_IP:5000/api/auto-scan/start
   ```

2. **Web arayüzünü açın:**
   ```
   http://YOUR_VPS_IP:5000
   ```

3. **Sistem 7/24 çalışacak!** 🚀

---

**🏆 Artık sisteminiz VPS'de 7/24 çalışarak otomatik sinyal üretiyor!**

