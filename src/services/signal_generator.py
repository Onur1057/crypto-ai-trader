import os
import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from src.services.coin_gecko_service import CoinGeckoService
from src.services.coin_filter_service import CoinFilterService
from src.services.advanced_signal_generator import advanced_signal_generator

class SignalGenerator:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.signals_file = os.path.join(self.data_dir, 'signals.json')
        self.history_file = os.path.join(self.data_dir, 'signal_history.json')
        
        self.coin_gecko = CoinGeckoService()
        self.coin_filter = CoinFilterService()
        
        # Gelişmiş sinyal üretici kullan
        self.advanced_generator = advanced_signal_generator
        
        self.signals = self.load_signals()
        self.signal_history = self.load_signal_history()
        
        # Otomatik güncelleme thread'i
        self.update_thread = None
        self.stop_updates = False
        
        print("🚀 Advanced Signal Generator başlatıldı")

    def load_signals(self) -> List[Dict]:
        """Aktif sinyalleri yükle"""
        try:
            if os.path.exists(self.signals_file):
                with open(self.signals_file, 'r', encoding='utf-8') as f:
                    signals = json.load(f)
                    print(f"📊 {len(signals)} aktif sinyal yüklendi")
                    return signals
        except Exception as e:
            print(f"❌ Sinyal yükleme hatası: {e}")
        return []

    def save_signals(self):
        """Aktif sinyalleri kaydet"""
        try:
            with open(self.signals_file, 'w', encoding='utf-8') as f:
                json.dump(self.signals, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Sinyal kaydetme hatası: {e}")

    def load_signal_history(self) -> List[Dict]:
        """Sinyal geçmişini yükle"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    print(f"📚 {len(history)} geçmiş sinyal yüklendi")
                    return history
        except Exception as e:
            print(f"❌ Geçmiş yükleme hatası: {e}")
        return []

    def save_signal_history(self):
        """Sinyal geçmişini kaydet"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.signal_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Geçmiş kaydetme hatası: {e}")

    def add_to_history(self, signal: Dict, close_reason: str, close_price: float):
        """Sinyali geçmişe ekle"""
        try:
            entry_price = signal['entry_price']
            
            # PnL hesaplama - DÜZELTİLDİ
            if signal['direction'].upper() == 'LONG':
                pnl_percentage = ((close_price - entry_price) / entry_price) * 100
            else:
                pnl_percentage = ((entry_price - close_price) / entry_price) * 100
            
            # PnL USD hesaplama - DÜZELTİLDİ (1000$ pozisyon varsayımı)
            position_size = 1000
            pnl_usd = (pnl_percentage / 100) * position_size
            
            # Aşırı PnL kontrolü - YENİ
            if abs(pnl_percentage) > 500:  # %500'den fazla PnL mantıksız
                print(f"⚠️ Aşırı PnL tespit edildi: {pnl_percentage:.2f}% - Sınırlandırılıyor")
                pnl_percentage = 500 if pnl_percentage > 0 else -500
                pnl_usd = (pnl_percentage / 100) * position_size

            historical_signal = {
                'id': signal['id'],
                'coin_symbol': signal['coin_symbol'],
                'direction': signal['direction'],
                'entry_price': entry_price,
                'close_price': close_price,
                'entry_time': signal['timestamp'],
                'close_time': datetime.now().isoformat(),
                'pnl_percentage': round(pnl_percentage, 2),
                'pnl_usd': round(pnl_usd, 2),
                'close_reason': close_reason,
                'confidence': signal['confidence'],
                'analysis': signal.get('analysis', ''),
                'tp_levels': signal.get('tp_levels', {}),
                'sl_level': signal.get('sl_level', 0),
                'duration_minutes': self.calculate_duration_minutes(signal['timestamp'])
            }
            
            self.signal_history.append(historical_signal)
            self.save_signal_history()
            
            print(f"📚 Sinyal geçmişe eklendi: {signal['coin_symbol']} - {close_reason} - PnL: {pnl_percentage:.2f}%")
            
        except Exception as e:
            print(f"❌ Geçmişe ekleme hatası: {e}")

    def calculate_duration_minutes(self, start_time: str) -> int:
        """Sinyal süresini dakika olarak hesapla"""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.now()
            duration = end - start
            return int(duration.total_seconds() / 60)
        except:
            return 0

    def generate_signals(self, coin_count: int = 10) -> List[Dict]:
        """Gelişmiş teknik analiz ile yeni sinyaller üret"""
        try:
            print(f"🔍 {coin_count} coin için gelişmiş teknik analiz başlatılıyor...")
            
            # Gelişmiş sinyal üretici kullan
            result = self.advanced_generator.generate_signals(coin_count)
            
            if result['success']:
                # Yeni sinyalleri mevcut sinyallere ekle
                new_signals = self.advanced_generator.get_signals()
                
                # Eski formatla uyumlu hale getir
                formatted_signals = []
                for signal in new_signals:
                    formatted_signal = {
                        'id': signal['id'],
                        'coin_symbol': signal['symbol'],
                        'coin_name': signal['symbol'],  # Coin name için symbol kullan
                        'direction': signal['direction'],
                        'entry_price': signal['entry_price'],
                        'current_price': signal['current_price'],
                        'confidence': signal['confidence'],
                        'analysis': signal.get('analysis_summary', ''),
                        'timestamp': signal['created_at'],
                        'status': 'Aktif',
                        'pnl_percentage': signal['pnl_percent'],
                        'pnl_usd': 0,  # USD hesaplaması için ayrı metod gerekli
                        'tp_levels': {
                            'tp1': signal.get('tp1'),
                            'tp2': signal.get('tp2')
                        },
                        'sl_level': signal.get('sl')
                    }
                    formatted_signals.append(formatted_signal)
                
                # Mevcut sinyalleri güncelle
                self.signals = formatted_signals
                self.save_signals()
                
                print(f"🎯 {result['new_signals']} yeni gelişmiş sinyal üretildi")
                return formatted_signals
            else:
                print("❌ Gelişmiş sinyal üretimi başarısız, eski sisteme geçiliyor...")
                return self._generate_signals_fallback(coin_count)
                
        except Exception as e:
            print(f"❌ Gelişmiş sinyal üretme hatası: {e}")
            print("🔄 Eski sisteme geçiliyor...")
            return self._generate_signals_fallback(coin_count)
    
    def _generate_signals_fallback(self, coin_count: int = 10) -> List[Dict]:
        """Yedek sinyal üretme sistemi (eski sistem)"""
        try:
            print(f"🔍 {coin_count} coin için yedek sinyal üretiliyor...")
            
            # Filtrelenmiş coinleri al
            filtered_coins = self.coin_filter.get_filtered_coins(limit=coin_count * 3)
            
            if not filtered_coins:
                print("❌ Filtrelenmiş coin bulunamadı")
                return []
            
            new_signals = []
            
            for coin_data in filtered_coins[:coin_count]:
                try:
                    coin_id = coin_data['id']
                    symbol = coin_data['symbol'].upper()
                    current_price = coin_data['current_price']
                    
                    # Wrapped coin kontrolü - GÜÇLENDİRİLDİ
                    wrapped_keywords = [
                        'wrapped', 'staked', 'liquid', 'restaked', 'bridged',
                        'wbtc', 'weth', 'wbnb', 'wmatic', 'wavax', 'wftm',
                        'steth', 'reth', 'cbeth', 'lseth', 'rseth', 'oseth', 'meth',
                        'cbbtc', 'bnsol', 'jitosol', 'msol', 'stsol'
                    ]
                    
                    coin_name_lower = coin_data['name'].lower()
                    symbol_lower = symbol.lower()
                    
                    is_wrapped = any(keyword in coin_name_lower or keyword in symbol_lower 
                                   for keyword in wrapped_keywords)
                    
                    if is_wrapped:
                        print(f"⚠️ Wrapped coin atlandı: {symbol} ({coin_data['name']})")
                        continue
                    
                    # Mevcut sinyallerde var mı kontrol et
                    existing_signal = next((s for s in self.signals if s['coin_symbol'] == symbol), None)
                    if existing_signal:
                        continue
                    
                    # Teknik analiz simülasyonu
                    analysis_result = self.simulate_technical_analysis(coin_data)
                    
                    if analysis_result['signal'] != 'HOLD':
                        signal = {
                            'id': f"{symbol}_{int(time.time())}",
                            'coin_symbol': symbol,
                            'coin_name': coin_data['name'],
                            'direction': analysis_result['signal'],
                            'entry_price': current_price,
                            'current_price': current_price,
                            'confidence': analysis_result['confidence'],
                            'analysis': analysis_result['analysis'],
                            'timestamp': datetime.now().isoformat(),
                            'status': 'Aktif',
                            'pnl_percentage': 0,
                            'pnl_usd': 0,
                            'tp_levels': analysis_result['tp_levels'],
                            'sl_level': analysis_result['sl_level']
                        }
                        
                        new_signals.append(signal)
                        print(f"✅ Yedek sinyal: {symbol} {analysis_result['signal']} @ ${current_price:.4f}")
                
                except Exception as e:
                    print(f"❌ {coin_data.get('symbol', 'Unknown')} için sinyal üretme hatası: {e}")
                    continue
            
            # Yeni sinyalleri mevcut listeye ekle
            self.signals.extend(new_signals)
            self.save_signals()
            
            print(f"🎯 {len(new_signals)} yeni sinyal üretildi")
            return new_signals
            
        except Exception as e:
            print(f"❌ Sinyal üretme hatası: {e}")
            return []

    def simulate_technical_analysis(self, coin_data: Dict) -> Dict:
        """Teknik analiz simülasyonu"""
        try:
            import random
            
            # Rastgele teknik analiz sonucu
            signals = ['LONG', 'SHORT', 'HOLD']
            weights = [0.35, 0.35, 0.30]  # %35 LONG, %35 SHORT, %30 HOLD
            
            signal = random.choices(signals, weights=weights)[0]
            
            if signal == 'HOLD':
                return {
                    'signal': 'HOLD',
                    'confidence': 0,
                    'analysis': 'Şu anda net bir sinyal yok',
                    'tp_levels': {},
                    'sl_level': 0
                }
            
            confidence = random.randint(75, 95)
            current_price = coin_data['current_price']
            
            # TP ve SL seviyeleri
            if signal == 'LONG':
                tp1 = current_price * 1.05  # %5
                tp2 = current_price * 1.12  # %12
                tp3 = current_price * 1.20  # %20
                sl = current_price * 0.92   # -%8
            else:  # SHORT
                tp1 = current_price * 0.95  # -%5
                tp2 = current_price * 0.88  # -%12
                tp3 = current_price * 0.80  # -%20
                sl = current_price * 1.08   # +%8
            
            analysis_texts = [
                f"{coin_data['symbol'].upper()} için kapsamlı teknik analiz sonucunda güçlü bir {'alım' if signal == 'LONG' else 'satım'} fırsatı tespit ettim.",
                f"{coin_data['symbol'].upper()} için piyasa dinamiklerini analiz ettiğimde güçlü bir momentum birikimi fark ediyorum.",
                f"{coin_data['symbol'].upper()}'nin mevcut piyasa yapısını derinlemesine inceledikten sonra {'yükseliş' if signal == 'LONG' else 'düşüş'} potansiyeli gözlemliyorum."
            ]
            
            return {
                'signal': signal,
                'confidence': confidence,
                'analysis': random.choice(analysis_texts),
                'tp_levels': {
                    'tp1': round(tp1, 6),
                    'tp2': round(tp2, 6),
                    'tp3': round(tp3, 6)
                },
                'sl_level': round(sl, 6)
            }
            
        except Exception as e:
            print(f"❌ Teknik analiz hatası: {e}")
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'analysis': 'Analiz hatası',
                'tp_levels': {},
                'sl_level': 0
            }

    def update_signal_prices(self):
        """Aktif sinyallerin fiyatlarını güncelle"""
        try:
            if not self.signals:
                return
            
            print(f"🔄 {len(self.signals)} sinyalin fiyatları güncelleniyor...")
            
            # Tüm coin sembollerini topla
            symbols = [signal['coin_symbol'].lower() for signal in self.signals]
            
            # Fiyatları toplu olarak al
            prices = self.coin_gecko.get_current_prices(symbols)
            
            if not prices:
                print("❌ Fiyat verisi alınamadı")
                return
            
            updated_count = 0
            signals_to_close = []
            
            for signal in self.signals:
                symbol_lower = signal['coin_symbol'].lower()
                
                if symbol_lower in prices:
                    old_price = signal['current_price']
                    new_price = prices[symbol_lower]
                    
                    if new_price and new_price > 0:
                        signal['current_price'] = new_price
                        entry_price = signal['entry_price']
                        
                        # PnL hesaplama - DÜZELTİLDİ
                        if signal['direction'].upper() == 'LONG':
                            pnl_percentage = ((new_price - entry_price) / entry_price) * 100
                        else:
                            pnl_percentage = ((entry_price - new_price) / entry_price) * 100
                        
                        # Aşırı PnL kontrolü - YENİ
                        if abs(pnl_percentage) > 500:
                            print(f"⚠️ {signal['coin_symbol']}: Aşırı PnL tespit edildi ({pnl_percentage:.2f}%) - Sinyal kapatılıyor")
                            signals_to_close.append((signal, 'extreme_pnl', new_price))
                            continue
                        
                        signal['pnl_percentage'] = round(pnl_percentage, 2)
                        
                        # PnL USD hesaplama - DÜZELTİLDİ
                        position_size = 1000  # $1000 pozisyon varsayımı
                        pnl_usd = (pnl_percentage / 100) * position_size
                        signal['pnl_usd'] = round(pnl_usd, 2)
                        
                        updated_count += 1
                        
                        # Fiyat değişimi logla
                        if abs(old_price - new_price) / old_price > 0.01:  # %1'den fazla değişim
                            print(f"💰 {signal['coin_symbol']}: ${old_price:.4f} → ${new_price:.4f} (PnL: {pnl_percentage:.2f}%)")
                        
                        # TP/SL kontrolü
                        tp_sl_result = self.check_tp_sl_levels(signal, new_price)
                        if tp_sl_result:
                            signals_to_close.append((signal, tp_sl_result, new_price))
            
            # Kapatılacak sinyalleri işle
            for signal, close_reason, close_price in signals_to_close:
                self.close_signal(signal, close_reason, close_price)
            
            if updated_count > 0:
                self.save_signals()
                print(f"✅ {updated_count} sinyal güncellendi")
            
        except Exception as e:
            print(f"❌ Fiyat güncelleme hatası: {e}")

    def check_tp_sl_levels(self, signal: Dict, current_price: float) -> Optional[str]:
        """TP/SL seviyelerini kontrol et"""
        try:
            tp_levels = signal.get('tp_levels', {})
            sl_level = signal.get('sl_level', 0)
            direction = signal['direction'].upper()
            
            if direction == 'LONG':
                # LONG pozisyon için TP kontrolü (fiyat yükselirse)
                if 'tp3' in tp_levels and current_price >= tp_levels['tp3']:
                    return 'tp3_hit'
                elif 'tp2' in tp_levels and current_price >= tp_levels['tp2']:
                    return 'tp2_hit'
                elif 'tp1' in tp_levels and current_price >= tp_levels['tp1']:
                    return 'tp1_hit'
                
                # LONG pozisyon için SL kontrolü (fiyat düşerse)
                if sl_level > 0 and current_price <= sl_level:
                    return 'stop_loss'
                    
            else:  # SHORT
                # SHORT pozisyon için TP kontrolü (fiyat düşerse)
                if 'tp3' in tp_levels and current_price <= tp_levels['tp3']:
                    return 'tp3_hit'
                elif 'tp2' in tp_levels and current_price <= tp_levels['tp2']:
                    return 'tp2_hit'
                elif 'tp1' in tp_levels and current_price <= tp_levels['tp1']:
                    return 'tp1_hit'
                
                # SHORT pozisyon için SL kontrolü (fiyat yükselirse)
                if sl_level > 0 and current_price >= sl_level:
                    return 'stop_loss'
            
            return None
            
        except Exception as e:
            print(f"❌ TP/SL kontrol hatası: {e}")
            return None

    def close_signal(self, signal: Dict, reason: str, close_price: float):
        """Sinyali kapat ve geçmişe ekle"""
        try:
            # Geçmişe ekle
            self.add_to_history(signal, reason, close_price)
            
            # Aktif listeden çıkar
            self.signals = [s for s in self.signals if s['id'] != signal['id']]
            
            # PnL hesapla
            entry_price = signal['entry_price']
            if signal['direction'].upper() == 'LONG':
                pnl_percentage = ((close_price - entry_price) / entry_price) * 100
            else:
                pnl_percentage = ((entry_price - close_price) / entry_price) * 100
            
            print(f"🔒 Sinyal kapatıldı: {signal['coin_symbol']} - {reason} - PnL: {pnl_percentage:.2f}%")
            
        except Exception as e:
            print(f"❌ Sinyal kapatma hatası: {e}")

    def get_active_signals(self) -> List[Dict]:
        """Aktif sinyalleri getir"""
        return self.signals.copy()

    def get_signal_history(self) -> List[Dict]:
        """Sinyal geçmişini getir"""
        return self.signal_history.copy()

    def get_performance_stats(self) -> Dict[str, any]:
        """Gelişmiş performans istatistiklerini getir"""
        try:
            # Gelişmiş sinyal üreticiden istatistikleri al
            advanced_stats = self.advanced_generator.get_performance_stats()
            
            # Eski sistem istatistikleri ile birleştir
            legacy_stats = self._get_legacy_performance_stats()
            
            # Birleştirilmiş istatistikler
            combined_stats = {
                'total_signals': advanced_stats['total_signals'] + legacy_stats['total_signals'],
                'active_signals': advanced_stats['active_signals'] + legacy_stats['active_signals'],
                'closed_signals': advanced_stats['closed_signals'] + legacy_stats['closed_signals'],
                'total_pnl': advanced_stats['total_pnl'] + legacy_stats['total_pnl'],
                'average_pnl': (advanced_stats['average_pnl'] + legacy_stats['average_pnl']) / 2,
                'success_rate': (advanced_stats['success_rate'] + legacy_stats['success_rate']) / 2,
                'profitable_signals': advanced_stats['profitable_signals'] + legacy_stats['profitable_signals'],
                'auto_scanning': advanced_stats['auto_scanning'],
                'analysis_type': 'ADVANCED_TECHNICAL',
                'system_status': 'ACTIVE'
            }
            
            return combined_stats
            
        except Exception as e:
            print(f"❌ Performans istatistik hatası: {e}")
            return self._get_legacy_performance_stats()
    
    def _get_legacy_performance_stats(self) -> Dict[str, any]:
        """Eski sistem performans istatistikleri"""
        try:
            total_signals = len(self.signal_history)
            active_signals = len(self.signals)
            
            if total_signals == 0:
                return {
                    'total_signals': active_signals,
                    'active_signals': active_signals,
                    'closed_signals': 0,
                    'success_rate': 0,
                    'total_pnl': 0,
                    'average_pnl': 0,
                    'profitable_signals': 0,
                    'auto_scanning': False
                }
            
            # Başarı oranı (pozitif PnL'li işlemler)
            successful_trades = [h for h in self.signal_history if h.get('pnl_percentage', 0) > 0]
            success_rate = (len(successful_trades) / total_signals) * 100
            
            # Toplam PnL
            total_pnl = sum(h.get('pnl_percentage', 0) for h in self.signal_history)
            
            # Ortalama PnL
            avg_pnl = total_pnl / total_signals if total_signals > 0 else 0
            
            return {
                'total_signals': total_signals + active_signals,
                'active_signals': active_signals,
                'closed_signals': total_signals,
                'success_rate': round(success_rate, 1),
                'total_pnl': round(total_pnl, 2),
                'average_pnl': round(avg_pnl, 2),
                'profitable_signals': len(successful_trades),
                'auto_scanning': False
            }
            
        except Exception as e:
            print(f"❌ Legacy performans istatistik hatası: {e}")
            return {
                'total_signals': 0,
                'active_signals': 0,
                'closed_signals': 0,
                'success_rate': 0,
                'total_pnl': 0,
                'average_pnl': 0,
                'profitable_signals': 0,
                'auto_scanning': False
            }
            
            return {
                'total_signals': total_signals + active_signals,
                'active_signals': active_signals,
                'closed_signals': total_signals,
                'success_rate': f'{success_rate:.1f}%',
                'total_pnl': f'${total_pnl_usd:.2f}',
                'avg_pnl': f'{avg_pnl:.1f}%',
                'best_trade': f"{best_trade['coin_symbol']} (+{best_trade.get('pnl_percentage', 0):.1f}%)",
                'worst_trade': f"{worst_trade['coin_symbol']} ({worst_trade.get('pnl_percentage', 0):.1f}%)"
            }
            
        except Exception as e:
            print(f"❌ İstatistik hesaplama hatası: {e}")
            return {
                'total_signals': len(self.signals),
                'active_signals': len(self.signals),
                'closed_signals': 0,
                'success_rate': '0.0%',
                'total_pnl': '$0.00',
                'avg_pnl': '0.0%',
                'best_trade': 'N/A',
                'worst_trade': 'N/A'
            }

    def clear_all_data(self):
        """Tüm verileri temizle"""
        try:
            self.signals = []
            self.signal_history = []
            self.save_signals()
            self.save_signal_history()
            print("🧹 Tüm veriler temizlendi")
        except Exception as e:
            print(f"❌ Veri temizleme hatası: {e}")

    def reset_system(self):
        """Sistemi tamamen sıfırla"""
        try:
            self.clear_all_data()
            
            # Dosyaları sil
            if os.path.exists(self.signals_file):
                os.remove(self.signals_file)
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
                
            print("🔄 Sistem tamamen sıfırlandı")
        except Exception as e:
            print(f"❌ Sistem sıfırlama hatası: {e}")

    def start_auto_updates(self):
        """Otomatik güncellemeleri başlat"""
        if self.update_thread and self.update_thread.is_alive():
            return
        
        self.stop_updates = False
        self.update_thread = threading.Thread(target=self._auto_update_loop, daemon=True)
        self.update_thread.start()
        print("🔄 Otomatik güncelleme başlatıldı")

    def stop_auto_updates(self):
        """Otomatik güncellemeleri durdur"""
        self.stop_updates = True
        if self.update_thread:
            self.update_thread.join(timeout=5)
        print("⏹️ Otomatik güncelleme durduruldu")

    def _auto_update_loop(self):
        """Otomatik güncelleme döngüsü"""
        while not self.stop_updates:
            try:
                self.update_signal_prices()
                time.sleep(30)  # 30 saniyede bir güncelle
            except Exception as e:
                print(f"❌ Otomatik güncelleme hatası: {e}")
                time.sleep(60)  # Hata durumunda 1 dakika bekle

    def get_performance_stats(self):
        """Performans istatistiklerini getir"""
        try:
            active_signals = len(self.signals)
            closed_signals = len(self.signal_history)
            
            # PnL hesaplamaları
            total_pnl = 0
            positive_trades = 0
            negative_trades = 0
            
            for signal in self.signal_history:
                if 'pnl_usd' in signal:
                    pnl = signal['pnl_usd']
                    total_pnl += pnl
                    if pnl > 0:
                        positive_trades += 1
                    else:
                        negative_trades += 1
            
            # Aktif sinyallerin PnL'ini de ekle
            for signal in self.signals:
                if 'pnl_usd' in signal:
                    total_pnl += signal['pnl_usd']
            
            success_rate = 0
            if closed_signals > 0:
                success_rate = (positive_trades / closed_signals) * 100
            
            return {
                'active_signals': active_signals,
                'closed_signals': closed_signals,
                'total_signals': active_signals + closed_signals,
                'total_pnl': round(total_pnl, 2),
                'total_pnl_usd': round(total_pnl, 2),
                'success_rate': round(success_rate, 2),
                'positive_trades': positive_trades,
                'negative_trades': negative_trades
            }
        except Exception as e:
            print(f"❌ Performans istatistikleri hatası: {e}")
            return {
                'active_signals': 0,
                'closed_signals': 0,
                'total_signals': 0,
                'total_pnl': 0,
                'total_pnl_usd': 0,
                'success_rate': 0,
                'positive_trades': 0,
                'negative_trades': 0
            }


# Global instance
signal_generator = SignalGenerator()

