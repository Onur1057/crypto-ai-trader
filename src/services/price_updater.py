"""
Otomatik Fiyat Güncelleme Servisi
Aktif sinyallerin fiyatlarını ve PnL değerlerini gerçek zamanlı günceller
"""

import threading
import time
import requests
from datetime import datetime

class PriceUpdater:
    def __init__(self, signal_generator):
        self.signal_generator = signal_generator
        self.running = False
        self.update_thread = None
        self.update_interval = 30  # 30 saniyede bir güncelle
        
    def start(self):
        """Otomatik fiyat güncellemeyi başlat"""
        if self.running:
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        print("🔄 Otomatik fiyat güncelleme başlatıldı (30 saniye aralık)")
        
    def stop(self):
        """Otomatik fiyat güncellemeyi durdur"""
        self.running = False
        if self.update_thread:
            self.update_thread.join()
        print("⏹️ Otomatik fiyat güncelleme durduruldu")
        
    def _update_loop(self):
        """Ana güncelleme döngüsü"""
        while self.running:
            try:
                self._update_all_signals()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"❌ Fiyat güncelleme döngüsü hatası: {e}")
                time.sleep(5)  # Hata durumunda kısa bekle
                
    def _update_all_signals(self):
        """Tüm aktif sinyallerin fiyatlarını güncelle"""
        try:
            signals = self.signal_generator.get_active_signals()
            if not signals:
                return
                
            print(f"🔄 {len(signals)} sinyalin fiyatları güncelleniyor...")
            
            # Tüm coin sembollerini topla
            symbols = []
            for signal in signals:
                symbol = signal.get('coin_symbol', '').lower()
                if symbol:
                    symbols.append(symbol)
            
            if not symbols:
                return
                
            # CoinGecko'dan fiyatları al
            prices = self._get_current_prices(symbols)
            
            if not prices:
                print("❌ Fiyat verisi alınamadı")
                return
            
            updated_count = 0
            total_pnl = 0
            
            for signal in signals:
                symbol_lower = signal.get('coin_symbol', '').lower()
                
                if symbol_lower in prices:
                    new_price = prices[symbol_lower]
                    
                    if new_price and new_price > 0:
                        old_price = signal.get('current_price', 0)
                        entry_price = signal.get('entry_price', 0)
                        
                        # Fiyatı güncelle
                        signal['current_price'] = new_price
                        
                        # PnL hesapla
                        if entry_price > 0:
                            if signal.get('direction', '').upper() == 'LONG':
                                pnl_percentage = ((new_price - entry_price) / entry_price) * 100
                            else:
                                pnl_percentage = ((entry_price - new_price) / entry_price) * 100
                            
                            signal['pnl_percentage'] = round(pnl_percentage, 2)
                            
                            # USD PnL hesapla (1000$ pozisyon varsayımı)
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
                self.signal_generator.save_signals()
                avg_pnl = total_pnl / updated_count
                print(f"✅ {updated_count} sinyal güncellendi - Ortalama PnL: {avg_pnl:+.2f}%")
                
        except Exception as e:
            print(f"❌ Sinyal güncelleme hatası: {e}")
            
    def _get_current_prices(self, symbols):
        """CoinGecko'dan güncel fiyatları al"""
        try:
            if not symbols:
                return {}
                
            # Sembolleri virgülle ayır
            symbols_str = ','.join(symbols)
            
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': symbols_str,
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                prices = {}
                
                for coin_id, price_data in data.items():
                    if 'usd' in price_data:
                        prices[coin_id] = price_data['usd']
                
                return prices
            else:
                print(f"❌ CoinGecko API hatası: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Fiyat alma hatası: {e}")
            return {}
            
    def force_update(self):
        """Manuel fiyat güncelleme"""
        print("🔄 Manuel fiyat güncelleme başlatılıyor...")
        self._update_all_signals()
        
    def get_status(self):
        """Güncelleme durumunu döndür"""
        return {
            'running': self.running,
            'interval': self.update_interval,
            'last_update': datetime.now().isoformat()
        }

