import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np

from .chart_data_service import chart_data_service
from .pattern_recognition_service import pattern_recognition_service
from .technical_analysis_service import technical_analysis_service
from .coin_filter_service import CoinFilterService

class AdvancedSignalGenerator:
    def __init__(self):
        self.signals = []
        self.signal_history = []
        self.coin_filter = CoinFilterService()
        
        # Analiz parametreleri
        self.timeframes = ['15m', '1h', '4h']  # Multi-timeframe analiz
        self.min_confidence = 60  # Minimum güven seviyesi
        self.max_signals_per_run = 5  # Her çalıştırmada max sinyal
        
        print("🚀 Advanced Signal Generator başlatıldı")
    
    def generate_signals(self, coin_count: int = 15) -> Dict[str, any]:
        """
        Gerçek teknik analiz ile sinyal üret
        
        Args:
            coin_count: Analiz edilecek coin sayısı
            
        Returns:
            Üretilen sinyaller ve istatistikler
        """
        try:
            print(f"🔍 {coin_count} coin için gelişmiş sinyal analizi başlatılıyor...")
            
            # Filtrelenmiş coinleri al
            filtered_coins = self.coin_filter.get_filtered_coins()
            if not filtered_coins:
                print("❌ Analiz için uygun coin bulunamadı")
                return {'new_signals': 0, 'total_signals': len(self.signals)}
            
            # Rastgele coin seç
            selected_coins = random.sample(filtered_coins, min(coin_count, len(filtered_coins)))
            print(f"📊 Seçilen coinler: {', '.join(selected_coins)}")
            
            new_signals = []
            analysis_results = []
            
            for symbol in selected_coins:
                try:
                    print(f"🔍 {symbol} analiz ediliyor...")
                    
                    # Multi-timeframe analiz
                    signal_data = self._analyze_coin_comprehensive(symbol)
                    
                    if signal_data and signal_data['confidence'] >= self.min_confidence:
                        # Yeni sinyal oluştur
                        new_signal = self._create_signal_from_analysis(symbol, signal_data)
                        if new_signal:
                            new_signals.append(new_signal)
                            analysis_results.append({
                                'symbol': symbol,
                                'analysis': signal_data
                            })
                            print(f"✅ {symbol} {new_signal['direction']} sinyali oluşturuldu (Güven: %{signal_data['confidence']})")
                    else:
                        print(f"⚠️ {symbol} için yeterli güven seviyesi yok")
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ {symbol} analiz hatası: {e}")
                    continue
            
            # Yeni sinyalleri ekle
            self.signals.extend(new_signals)
            
            # Eski sinyalleri temizle (24 saatten eski)
            self._cleanup_old_signals()
            
            print(f"🎯 {len(new_signals)} yeni sinyal üretildi")
            
            return {
                'new_signals': len(new_signals),
                'total_signals': len(self.signals),
                'analysis_results': analysis_results,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Sinyal üretme hatası: {e}")
            return {'new_signals': 0, 'total_signals': len(self.signals), 'success': False}
    
    def _analyze_coin_comprehensive(self, symbol: str) -> Optional[Dict[str, any]]:
        """
        Coin için kapsamlı analiz (Multi-timeframe + Pattern + Technical)
        
        Args:
            symbol: Coin sembolü
            
        Returns:
            Analiz sonuçları
        """
        try:
            # Multi-timeframe veri al
            timeframe_data = chart_data_service.get_multiple_timeframes(
                symbol, self.timeframes, limit=100
            )
            
            if not timeframe_data:
                print(f"❌ {symbol} için grafik verisi alınamadı")
                return None
            
            # Her timeframe için analiz
            timeframe_analyses = {}
            all_signals = []
            confidence_scores = []
            
            for tf, df in timeframe_data.items():
                try:
                    # Pattern recognition
                    pattern_analysis = pattern_recognition_service.analyze_patterns(df)
                    
                    # Technical indicators
                    technical_analysis = technical_analysis_service.analyze_indicators(df)
                    
                    # Timeframe analizi birleştir
                    tf_analysis = {
                        'timeframe': tf,
                        'pattern': pattern_analysis,
                        'technical': technical_analysis,
                        'data_points': len(df)
                    }
                    
                    timeframe_analyses[tf] = tf_analysis
                    
                    # Sinyalleri topla
                    if pattern_analysis['signal'] != 'HOLD':
                        all_signals.append(pattern_analysis['signal'])
                        confidence_scores.append(pattern_analysis['confidence'])
                    
                    if technical_analysis['signal'] != 'HOLD':
                        all_signals.append(technical_analysis['signal'])
                        confidence_scores.append(technical_analysis['confidence'])
                    
                    print(f"  📈 {tf}: Pattern={pattern_analysis['signal']} (%{pattern_analysis['confidence']}), Technical={technical_analysis['signal']} (%{technical_analysis['confidence']})")
                    
                except Exception as e:
                    print(f"❌ {symbol} {tf} analiz hatası: {e}")
                    continue
            
            # Final sinyal hesapla
            final_signal, final_confidence = self._calculate_multi_timeframe_signal(
                all_signals, confidence_scores, timeframe_analyses
            )
            
            # Son fiyatı al
            current_price = chart_data_service.get_latest_price(symbol)
            
            return {
                'symbol': symbol,
                'signal': final_signal,
                'confidence': final_confidence,
                'current_price': current_price,
                'timeframe_analyses': timeframe_analyses,
                'total_signals': len(all_signals),
                'analysis_summary': self._generate_analysis_summary(timeframe_analyses, final_signal)
            }
            
        except Exception as e:
            print(f"❌ {symbol} kapsamlı analiz hatası: {e}")
            return None
    
    def _calculate_multi_timeframe_signal(self, signals: List[str], confidences: List[int], 
                                        timeframe_analyses: Dict) -> Tuple[str, int]:
        """
        Multi-timeframe sinyallerini birleştir
        
        Args:
            signals: Tüm sinyaller listesi
            confidences: Güven seviyeleri
            timeframe_analyses: Timeframe analizleri
            
        Returns:
            Final sinyal ve güven seviyesi
        """
        try:
            if not signals:
                return 'HOLD', 50
            
            # Timeframe ağırlıkları (uzun vadeli daha önemli)
            timeframe_weights = {
                '15m': 1.0,
                '1h': 1.2,
                '4h': 1.5,
                '1d': 2.0
            }
            
            weighted_long = 0
            weighted_short = 0
            total_weight = 0
            
            # Her timeframe için ağırlıklı hesaplama
            for tf, analysis in timeframe_analyses.items():
                weight = timeframe_weights.get(tf, 1.0)
                
                # Pattern sinyali
                pattern_signal = analysis['pattern']['signal']
                pattern_confidence = analysis['pattern']['confidence']
                
                if pattern_signal == 'LONG':
                    weighted_long += weight * pattern_confidence
                elif pattern_signal == 'SHORT':
                    weighted_short += weight * pattern_confidence
                
                # Technical sinyali
                technical_signal = analysis['technical']['signal']
                technical_confidence = analysis['technical']['confidence']
                
                if technical_signal == 'LONG':
                    weighted_long += weight * technical_confidence
                elif technical_signal == 'SHORT':
                    weighted_short += weight * technical_confidence
                
                total_weight += weight * 2  # Her timeframe için 2 sinyal (pattern + technical)
            
            # Final sinyal
            if weighted_long > weighted_short:
                final_signal = 'LONG'
                final_confidence = min(95, int(weighted_long / total_weight * 100)) if total_weight > 0 else 60
            elif weighted_short > weighted_long:
                final_signal = 'SHORT'
                final_confidence = min(95, int(weighted_short / total_weight * 100)) if total_weight > 0 else 60
            else:
                final_signal = 'HOLD'
                final_confidence = 50
            
            # Confluence bonus (birden fazla timeframe aynı yönde)
            long_count = signals.count('LONG')
            short_count = signals.count('SHORT')
            
            if (final_signal == 'LONG' and long_count >= 3) or (final_signal == 'SHORT' and short_count >= 3):
                final_confidence = min(95, final_confidence + 10)
            
            return final_signal, final_confidence
            
        except Exception as e:
            print(f"❌ Multi-timeframe sinyal hesaplama hatası: {e}")
            return 'HOLD', 50
    
    def _create_signal_from_analysis(self, symbol: str, analysis_data: Dict) -> Optional[Dict[str, any]]:
        """
        Analiz sonucundan sinyal oluştur
        
        Args:
            symbol: Coin sembolü
            analysis_data: Analiz sonuçları
            
        Returns:
            Sinyal dictionary'si
        """
        try:
            current_price = analysis_data.get('current_price')
            if not current_price:
                return None
            
            signal_direction = analysis_data['signal']
            confidence = analysis_data['confidence']
            
            # TP ve SL hesapla (ATR bazlı)
            tp1, tp2, sl = self._calculate_targets_and_stops(
                current_price, signal_direction, analysis_data
            )
            
            # Sinyal oluştur
            signal = {
                'id': f"{symbol}_{int(time.time())}",
                'coin_symbol': symbol,
                'coin_id': self._get_coin_id_from_symbol(symbol),  # YENİ: coin_id eklendi
                'direction': signal_direction,
                'entry_price': current_price,
                'current_price': current_price,
                'tp1': tp1,
                'tp2': tp2,
                'sl': sl,
                'confidence': confidence,
                'pnl_percent': 0.0,
                'pnl_percentage': 0.0,  # YENİ: API uyumluluğu için
                'pnl_usd': 0.0,  # YENİ: USD PnL
                'status': 'ACTIVE',
                'created_at': datetime.now().isoformat(),
                'timeframe_count': len(analysis_data.get('timeframe_analyses', {})),
                'signal_count': analysis_data.get('total_signals', 0),
                'analysis_summary': analysis_data.get('analysis_summary', ''),
                'analysis_type': 'ADVANCED_TECHNICAL'
            }
            
            return signal
            
        except Exception as e:
            print(f"❌ Sinyal oluşturma hatası: {e}")
            return None
    
    def _calculate_targets_and_stops(self, entry_price: float, direction: str, 
                                   analysis_data: Dict) -> Tuple[float, float, float]:
        """
        TP ve SL seviyelerini hesapla
        
        Args:
            entry_price: Giriş fiyatı
            direction: Sinyal yönü
            analysis_data: Analiz verileri
            
        Returns:
            TP1, TP2, SL
        """
        try:
            # ATR bazlı hesaplama (varsayılan %2 volatilite)
            atr_percent = 2.0
            
            # Timeframe analizlerinden ATR al
            for tf_analysis in analysis_data.get('timeframe_analyses', {}).values():
                technical = tf_analysis.get('technical', {})
                indicators = technical.get('indicators', {})
                atr_data = indicators.get('atr', {})
                
                if 'atr_percent' in atr_data:
                    atr_percent = max(1.0, atr_data['atr_percent'])
                    break
            
            # Risk/Reward oranı
            risk_percent = max(1.5, atr_percent * 0.8)  # SL: ATR'nin %80'i
            reward1_percent = risk_percent * 1.5  # TP1: 1.5R
            reward2_percent = risk_percent * 3.0  # TP2: 3R
            
            if direction == 'LONG':
                tp1 = entry_price * (1 + reward1_percent / 100)
                tp2 = entry_price * (1 + reward2_percent / 100)
                sl = entry_price * (1 - risk_percent / 100)
            else:  # SHORT
                tp1 = entry_price * (1 - reward1_percent / 100)
                tp2 = entry_price * (1 - reward2_percent / 100)
                sl = entry_price * (1 + risk_percent / 100)
            
            return round(tp1, 8), round(tp2, 8), round(sl, 8)
            
        except Exception as e:
            print(f"❌ TP/SL hesaplama hatası: {e}")
            # Varsayılan değerler
            if direction == 'LONG':
                return (
                    round(entry_price * 1.03, 8),  # +3% TP1
                    round(entry_price * 1.06, 8),  # +6% TP2
                    round(entry_price * 0.98, 8)   # -2% SL
                )
            else:
                return (
                    round(entry_price * 0.97, 8),  # -3% TP1
                    round(entry_price * 0.94, 8),  # -6% TP2
                    round(entry_price * 1.02, 8)   # +2% SL
                )
    
    def _generate_analysis_summary(self, timeframe_analyses: Dict, final_signal: str) -> str:
        """
        Analiz özeti oluştur
        
        Args:
            timeframe_analyses: Timeframe analizleri
            final_signal: Final sinyal
            
        Returns:
            Analiz özeti metni
        """
        try:
            detected_patterns = []
            strong_indicators = []
            
            for tf, analysis in timeframe_analyses.items():
                # Pattern'leri topla
                patterns = analysis['pattern'].get('patterns', [])
                for pattern in patterns:
                    if pattern.get('detected', False):
                        pattern_name = pattern.get('pattern', '').replace('_', ' ').title()
                        detected_patterns.append(f"{pattern_name} ({tf})")
                
                # Güçlü teknik göstergeleri topla
                technical = analysis['technical']
                indicators = technical.get('indicators', {})
                
                for indicator_name, indicator_data in indicators.items():
                    if indicator_data.get('confidence', 0) >= 75:
                        strong_indicators.append(f"{indicator_name.upper()} ({tf})")
            
            # Özet metni oluştur
            summary = f"Multi-timeframe analiz sonucu: {final_signal} sinyali. "
            
            if detected_patterns:
                summary += f"Tespit edilen formasyonlar: {', '.join(detected_patterns[:3])}. "
            
            if strong_indicators:
                summary += f"Güçlü göstergeler: {', '.join(strong_indicators[:3])}. "
            
            summary += f"Toplam {len(timeframe_analyses)} timeframe analiz edildi."
            
            return summary
            
        except Exception as e:
            return f"Kapsamlı teknik analiz tamamlandı. {final_signal} sinyali tespit edildi."
    
    def _cleanup_old_signals(self):
        """24 saatten eski sinyalleri temizle"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=24)
            
            active_signals = []
            closed_signals = []
            
            for signal in self.signals:
                created_at = datetime.fromisoformat(signal['created_at'])
                
                if created_at > cutoff_time:
                    active_signals.append(signal)
                else:
                    # Eski sinyali kapalı sinyallere taşı
                    signal['status'] = 'EXPIRED'
                    signal['closed_at'] = current_time.isoformat()
                    closed_signals.append(signal)
            
            # Kapalı sinyalleri geçmişe ekle
            self.signal_history.extend(closed_signals)
            
            # Aktif sinyalleri güncelle
            self.signals = active_signals
            
            if closed_signals:
                print(f"🧹 {len(closed_signals)} eski sinyal temizlendi")
                
        except Exception as e:
            print(f"❌ Sinyal temizleme hatası: {e}")
    
    def update_signal_prices(self):
        """Aktif sinyallerin fiyatlarını güncelle"""
        try:
            for signal in self.signals:
                try:
                    symbol = signal['symbol']
                    current_price = chart_data_service.get_latest_price(symbol)
                    
                    if current_price:
                        signal['current_price'] = current_price
                        
                        # PnL hesapla
                        entry_price = signal['entry_price']
                        direction = signal['direction']
                        
                        if direction == 'LONG':
                            pnl_percent = ((current_price - entry_price) / entry_price) * 100
                        else:  # SHORT
                            pnl_percent = ((entry_price - current_price) / entry_price) * 100
                        
                        signal['pnl_percent'] = round(pnl_percent, 2)
                        
                        # TP/SL kontrolü
                        self._check_tp_sl_hit(signal)
                        
                except Exception as e:
                    print(f"❌ {signal.get('symbol', 'Unknown')} fiyat güncelleme hatası: {e}")
                    
        except Exception as e:
            print(f"❌ Sinyal fiyat güncelleme hatası: {e}")
    
    def _check_tp_sl_hit(self, signal: Dict):
        """TP veya SL'ye değip değmediğini kontrol et"""
        try:
            current_price = signal['current_price']
            direction = signal['direction']
            tp1 = signal.get('tp1')
            tp2 = signal.get('tp2')
            sl = signal.get('sl')
            
            if direction == 'LONG':
                # LONG pozisyon için TP/SL kontrolü
                if sl and current_price <= sl:
                    signal['status'] = 'CLOSED_SL'
                    signal['closed_at'] = datetime.now().isoformat()
                elif tp2 and current_price >= tp2:
                    signal['status'] = 'CLOSED_TP2'
                    signal['closed_at'] = datetime.now().isoformat()
                elif tp1 and current_price >= tp1:
                    signal['status'] = 'CLOSED_TP1'
                    signal['closed_at'] = datetime.now().isoformat()
            else:  # SHORT
                # SHORT pozisyon için TP/SL kontrolü
                if sl and current_price >= sl:
                    signal['status'] = 'CLOSED_SL'
                    signal['closed_at'] = datetime.now().isoformat()
                elif tp2 and current_price <= tp2:
                    signal['status'] = 'CLOSED_TP2'
                    signal['closed_at'] = datetime.now().isoformat()
                elif tp1 and current_price <= tp1:
                    signal['status'] = 'CLOSED_TP1'
                    signal['closed_at'] = datetime.now().isoformat()
                    
        except Exception as e:
            print(f"❌ TP/SL kontrol hatası: {e}")
    
    def get_signals(self) -> List[Dict[str, any]]:
        """Aktif sinyalleri getir"""
        return self.signals
    
    def get_signal_history(self) -> List[Dict[str, any]]:
        """Sinyal geçmişini getir"""
        return self.signal_history
    
    def get_performance_stats(self) -> Dict[str, any]:
        """Performans istatistiklerini getir"""
        try:
            total_signals = len(self.signals) + len(self.signal_history)
            active_signals = len(self.signals)
            closed_signals = len(self.signal_history)
            
            # PnL hesapla
            total_pnl = sum(signal.get('pnl_percent', 0) for signal in self.signals)
            avg_pnl = total_pnl / len(self.signals) if self.signals else 0
            
            # Başarı oranı (kapalı sinyaller için)
            profitable_signals = len([s for s in self.signal_history if s.get('pnl_percent', 0) > 0])
            success_rate = (profitable_signals / closed_signals * 100) if closed_signals > 0 else 0
            
            return {
                'total_signals': total_signals,
                'active_signals': active_signals,
                'closed_signals': closed_signals,
                'total_pnl': round(total_pnl, 2),
                'average_pnl': round(avg_pnl, 2),
                'success_rate': round(success_rate, 1),
                'profitable_signals': profitable_signals,
                'auto_scanning': False  # Manuel kontrol için
            }
            
        except Exception as e:
            print(f"❌ Performans istatistik hatası: {e}")
            return {
                'total_signals': 0,
                'active_signals': 0,
                'closed_signals': 0,
                'total_pnl': 0,
                'average_pnl': 0,
                'success_rate': 0,
                'profitable_signals': 0,
                'auto_scanning': False
            }

    def _get_coin_id_from_symbol(self, symbol: str) -> str:
        """
        Symbol'den CoinGecko coin_id'sini al
        
        Args:
            symbol: Coin sembolü (örn: BTC, ETH)
            
        Returns:
            CoinGecko coin_id (örn: bitcoin, ethereum)
        """
        try:
            # Kapsamlı symbol-to-id mapping
            symbol_to_id = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'ADA': 'cardano',
                'SOL': 'solana',
                'XRP': 'ripple',
                'DOT': 'polkadot',
                'DOGE': 'dogecoin',
                'AVAX': 'avalanche-2',
                'MATIC': 'matic-network',
                'LINK': 'chainlink',
                'UNI': 'uniswap',
                'LTC': 'litecoin',
                'BCH': 'bitcoin-cash',
                'XLM': 'stellar',
                'VET': 'vechain',
                'FIL': 'filecoin',
                'TRX': 'tron',
                'ETC': 'ethereum-classic',
                'ATOM': 'cosmos',
                'CRO': 'crypto-com-chain',
                'ALGO': 'algorand',
                'MANA': 'decentraland',
                'SAND': 'the-sandbox',
                'AXS': 'axie-infinity',
                'THETA': 'theta-token',
                'ICP': 'internet-computer',
                'FLOW': 'flow',
                'EGLD': 'elrond-erd-2',
                'XTZ': 'tezos',
                'AAVE': 'aave',
                'MKR': 'maker',
                'COMP': 'compound-governance-token',
                'YFI': 'yearn-finance',
                'SUSHI': 'sushi',
                'SNX': 'havven',
                'CRV': 'curve-dao-token',
                'BAL': 'balancer',
                'REN': 'republic-protocol',
                'ZRX': '0x',
                'OMG': 'omisego',
                'BAT': 'basic-attention-token',
                'ZIL': 'zilliqa',
                'ENJ': 'enjincoin',
                'HOT': 'holo',
                'ICX': 'icon',
                'QTUM': 'qtum',
                'ONT': 'ontology',
                'ZEC': 'zcash',
                'DASH': 'dash',
                'XMR': 'monero',
                'DCR': 'decred',
                'LSK': 'lisk',
                'NANO': 'nano',
                'DGB': 'digibyte',
                'RVN': 'ravencoin',
                'SC': 'siacoin',
                'DENT': 'dent',
                'STORJ': 'storj',
                'ANKR': 'ankr',
                'CELR': 'celer-network',
                'COTI': 'coti',
                'CTSI': 'cartesi',
                'BAND': 'band-protocol',
                'OCEAN': 'ocean-protocol',
                'NKN': 'nkn',
                'IOTX': 'iotex',
                'FET': 'fetch-ai',
                'AGIX': 'singularitynet',
                'RENDER': 'render-token',
                'TAO': 'bittensor',
                'PEPE': 'pepe',
                'BONK': 'bonk',
                'SHIB': 'shiba-inu',
                'FLOKI': 'floki',
                'WIF': 'dogwifcoin',
                'PENGU': 'pudgy-penguins',
                'SPX': 'spx6900',
                'TRUMP': 'maga',
                'PNUT': 'peanut-the-squirrel',
                'GOAT': 'goatseus-maximus',
                'ACT': 'achain',
                'NEIRO': 'neiro-ethereum',
                'POPCAT': 'popcat',
                'FARTCOIN': 'fartcoin',
                'AI16Z': 'ai16z',
                'VIRTUAL': 'virtual-protocol',
                'ZEREBRO': 'zerebro',
                'GRIFFAIN': 'griffain',
                'MOODENG': 'moo-deng',
                'CHILLGUY': 'just-a-chill-guy',
                'PUPS': 'bitcoin-puppets',
                'RUNES': 'runes',
                'ORDI': 'ordinals'
            }
            
            symbol_upper = symbol.upper()
            
            if symbol_upper in symbol_to_id:
                return symbol_to_id[symbol_upper]
            else:
                # Fallback: symbol'ü lowercase yapıp coin_id olarak kullan
                return symbol.lower()
                
        except Exception as e:
            print(f"❌ Symbol-to-ID dönüşüm hatası: {e}")
            return symbol.lower()

# Singleton instance
advanced_signal_generator = AdvancedSignalGenerator()

