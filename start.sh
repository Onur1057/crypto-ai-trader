#!/bin/bash

# Crypto AI Trader - Production Start Script
# Bu script sistemi production modunda başlatır

echo "🚀 Crypto AI Trader - Production Deployment"
echo "============================================"

# Proje dizinine git
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)
echo "📁 Proje Dizini: $PROJECT_DIR"

# Python path'i ayarla
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
echo "🐍 Python Path: $PYTHONPATH"

# Gerekli paketlerin kurulu olup olmadığını kontrol et
echo "📦 Gerekli paketler kontrol ediliyor..."
python3 -c "import flask, flask_cors, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Gerekli paketler eksik. Kuruluyor..."
    pip3 install -r requirements.txt
    pip3 install gunicorn
fi

# Eski process'leri temizle
echo "🧹 Eski process'ler temizleniyor..."
pkill -f "gunicorn.*crypto-ai-trader" 2>/dev/null || true
pkill -f "python.*main.py" 2>/dev/null || true

# PID dosyasını temizle
rm -f /tmp/crypto-ai-trader.pid

# Sistem durumunu kontrol et
echo "🔍 Sistem durumu kontrol ediliyor..."
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from src.services.coin_gecko_service import CoinGeckoService
    service = CoinGeckoService()
    print('✅ CoinGecko Service: OK')
except Exception as e:
    print(f'⚠️  CoinGecko Service: {e}')
"

# Production modunda başlat
echo "🚀 Production modunda başlatılıyor..."
echo "📊 URL: http://0.0.0.0:5000"
echo "🔗 Public URL: Bu URL deployment sonrası verilecek"
echo ""
echo "Durdurmak için: Ctrl+C veya pkill -f crypto-ai-trader"
echo ""

# Gunicorn ile başlat
exec gunicorn \
    --config gunicorn.conf.py \
    --chdir "$PROJECT_DIR" \
    wsgi:application

