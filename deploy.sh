#!/bin/bash

# Crypto AI Backend Deployment Script
# Bu script VPS'inize 7/24 çalışan backend sistemi kurar

echo "🚀 Crypto AI Backend Deployment Başlatılıyor..."

# Sistem güncellemesi
echo "📦 Sistem güncelleniyor..."
apt update && apt upgrade -y

# Docker kurulumu (eğer yoksa)
if ! command -v docker &> /dev/null; then
    echo "🐳 Docker kuruluyor..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
else
    echo "✅ Docker zaten kurulu"
fi

# Docker Compose kurulumu (eğer yoksa)
if ! command -v docker-compose &> /dev/null; then
    echo "🔧 Docker Compose kuruluyor..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "✅ Docker Compose zaten kurulu"
fi

# Eski container'ı durdur ve kaldır (eğer varsa)
echo "🛑 Eski container'lar temizleniyor..."
docker-compose down 2>/dev/null || true
docker system prune -f

# Yeni container'ı build et ve başlat
echo "🏗️ Container build ediliyor..."
docker-compose build --no-cache

echo "🚀 Container başlatılıyor..."
docker-compose up -d

# Container durumunu kontrol et
echo "📊 Container durumu kontrol ediliyor..."
sleep 10
docker-compose ps

# Health check
echo "🏥 Health check yapılıyor..."
sleep 20
curl -f http://localhost:5000/api/health || echo "❌ Health check başarısız"

# Logları göster
echo "📋 Son loglar:"
docker-compose logs --tail=20

echo ""
echo "🎉 DEPLOYMENT TAMAMLANDI!"
echo ""
echo "📊 Sistem Bilgileri:"
echo "  - Backend URL: http://$(curl -s ifconfig.me):5000"
echo "  - API Health: http://$(curl -s ifconfig.me):5000/api/health"
echo "  - Container: crypto-ai-backend"
echo ""
echo "🔧 Yönetim Komutları:"
echo "  - Logları görüntüle: docker-compose logs -f"
echo "  - Container'ı durdur: docker-compose down"
echo "  - Container'ı başlat: docker-compose up -d"
echo "  - Container durumu: docker-compose ps"
echo ""
echo "🎯 Otomatik taramayı başlatmak için:"
echo "  curl -X POST http://$(curl -s ifconfig.me):5000/api/auto-scan/start"
echo ""
echo "✅ Sistem 7/24 çalışmaya hazır!"

