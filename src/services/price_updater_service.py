"""
Otomatik PnL Güncelleme Servisi
Aktif sinyallerin fiyatlarını ve PnL değerlerini gerçek zamanlı günceller
"""

import threading
import time
import requests
from datetime import datetime
from src.services.signal_generator import signal_generator
from src.services.coin_gecko_service import coin_gecko_service

class PriceUpdaterService:
    def __init__(self):
        self.running = False
        self.update_thread = None
        self.update_interval = 30  # 30 saniyede bir güncelle
        
    def start(self):
        """Otomatik fiyat güncellemeyi başlat"""
        if self.running:
            print("⚠️ Otomatik fiyat güncelleme zaten çalışıyor")
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        print("🔄 Otomatik PnL güncelleme başlatıldı (30 saniye aralık)")
        
    def stop(self):
        """Otomatik fiyat güncellemeyi durdur"""
        self.running = False
        if self.update_thread:
            self.update_thread.join()
        print("⏹️ Otomatik PnL güncelleme durduruldu")
        
    def _update_loop(self):
        """Ana güncelleme döngüsü"""
        while self.running:
            try:
                self._update_all_signals()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"❌ PnL güncelleme döngüsü hatası: {e}")
                time.sleep(5)  # Hata durumunda kısa bekle
                
    def _update_all_signals(self):
        """Tüm aktif sinyallerin fiyatlarını güncelle"""
        try:
            active_signals = signal_generator.get_active_signals()
            if not active_signals:
                return
                
            print(f"🔄 {len(active_signals)} sinyalin PnL'i güncelleniyor...")
            
            # Coin sembollerini topla
            symbols = [s.get('coin_symbol', s.get('symbol', '')) for s in active_signals if s.get('coin_symbol') or s.get('symbol')]
            
            if not symbols:
                print("❌ Sinyallerde coin_symbol bulunamadı")
                return
                
            # CoinGecko'dan fiyatları al
            price_updates = coin_gecko_service.get_current_prices(symbols)
            
            if not price_updates:
                print("❌ Fiyat verisi alınamadı")
                return
            
            updated_count = 0
            total_pnl = 0
            
            for signal in active_signals:
                symbol = signal.get('coin_symbol', signal.get('symbol', '')).lower()
                
                if symbol in price_updates:
                    old_price = signal.get('current_price', 0)
                    new_price = price_updates[symbol]
                    
                    if new_price and new_price > 0:
                        signal['current_price'] = new_price
                        entry_price = signal.get('entry_price', 0)
                        
                        # PnL hesaplama
                        if entry_price > 0:
                            if signal.get('direction', '').upper() == 'LONG':
                                pnl_percentage = ((new_price - entry_price) / entry_price) * 100
                            else:
                                pnl_percentage = ((entry_price - new_price) / entry_price) * 100
                            
                            signal['pnl_percentage'] = round(pnl_percentage, 2)
                            
                            # USD PnL hesaplama (1000$ pozisyon varsayımı)
                            position_size = 1000
                            pnl_usd = (pnl_percentage / 100) * position_size
                            signal['pnl_usd'] = round(pnl_usd, 2)
                            
                            total_pnl += pnl_percentage
                            updated_count += 1
                            
                            # Önemli fiyat değişimlerini logla
                            if old_price > 0 and abs(old_price - new_price) / old_price > 0.02:  # %2'den fazla
                                print(f"💰 {signal['coin_symbol']}: ${old_price:.4f} → ${new_price:.4f} (PnL: {pnl_percentage:+.2f}%)")
            
            if updated_count > 0:
                # Sinyalleri kaydet
                signal_generator.save_signals()
                avg_pnl = total_pnl / updated_count
                print(f"✅ {updated_count} sinyal güncellendi - Ortalama PnL: {avg_pnl:+.2f}%")
                
        except Exception as e:
            print(f"❌ Sinyal güncelleme hatası: {e}")
            
    def force_update(self):
        """Manuel fiyat güncelleme"""
        print("🔄 Manuel PnL güncelleme başlatılıyor...")
        self._update_all_signals()
        
    def get_status(self):
        """Güncelleme durumunu döndür"""
        return {
            'running': self.running,
            'interval': self.update_interval,
            'last_update': datetime.now().isoformat()
        }

# Singleton instance
price_updater_service = PriceUpdaterService()

