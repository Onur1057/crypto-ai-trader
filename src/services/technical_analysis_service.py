import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class TechnicalAnalysisService:
    def __init__(self):
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.stoch_oversold = 20
        self.stoch_overbought = 80
        
        print("📈 Technical Analysis Service başlatıldı")
    
    def analyze_indicators(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Tüm teknik göstergeleri analiz et ve sinyal üret
        
        Args:
            df: OHLCV + teknik göstergeler DataFrame
            
        Returns:
            Teknik analiz sonuçları
        """
        try:
            if df is None or len(df) < 20:
                return {'signal': 'HOLD', 'confidence': 0, 'indicators': {}}
            
            indicators = {}
            signals = []
            
            # 1. RSI Analizi
            rsi_analysis = self.analyze_rsi(df)
            indicators['rsi'] = rsi_analysis
            if rsi_analysis['signal'] != 'HOLD':
                signals.append(rsi_analysis['signal'])
            
            # 2. MACD Analizi
            macd_analysis = self.analyze_macd(df)
            indicators['macd'] = macd_analysis
            if macd_analysis['signal'] != 'HOLD':
                signals.append(macd_analysis['signal'])
            
            # 3. Bollinger Bands Analizi
            bb_analysis = self.analyze_bollinger_bands(df)
            indicators['bollinger'] = bb_analysis
            if bb_analysis['signal'] != 'HOLD':
                signals.append(bb_analysis['signal'])
            
            # 4. Moving Average Analizi
            ma_analysis = self.analyze_moving_averages(df)
            indicators['moving_averages'] = ma_analysis
            if ma_analysis['signal'] != 'HOLD':
                signals.append(ma_analysis['signal'])
            
            # 5. Stochastic Analizi
            stoch_analysis = self.analyze_stochastic(df)
            indicators['stochastic'] = stoch_analysis
            if stoch_analysis['signal'] != 'HOLD':
                signals.append(stoch_analysis['signal'])
            
            # 6. Volume Analizi
            volume_analysis = self.analyze_volume(df)
            indicators['volume'] = volume_analysis
            
            # 7. ATR (Volatilite) Analizi
            atr_analysis = self.analyze_atr(df)
            indicators['atr'] = atr_analysis
            
            # Final sinyal hesapla
            final_signal, confidence = self._calculate_technical_signal(signals, indicators)
            
            return {
                'signal': final_signal,
                'confidence': confidence,
                'indicators': indicators,
                'summary': self._generate_technical_summary(indicators, final_signal)
            }
            
        except Exception as e:
            print(f"❌ Teknik analiz hatası: {e}")
            return {'signal': 'HOLD', 'confidence': 0, 'indicators': {}}
    
    def analyze_rsi(self, df: pd.DataFrame) -> Dict[str, any]:
        """RSI analizi"""
        try:
            if 'RSI_14' not in df.columns:
                return {'signal': 'HOLD', 'value': None, 'status': 'No data'}
            
            rsi = df['RSI_14'].iloc[-1]
            prev_rsi = df['RSI_14'].iloc[-2] if len(df) > 1 else rsi
            
            # RSI sinyali
            if rsi < self.rsi_oversold:
                signal = 'LONG'
                status = 'Oversold'
                confidence = min(90, 60 + (self.rsi_oversold - rsi))
            elif rsi > self.rsi_overbought:
                signal = 'SHORT'
                status = 'Overbought'
                confidence = min(90, 60 + (rsi - self.rsi_overbought))
            else:
                signal = 'HOLD'
                status = 'Neutral'
                confidence = 50
            
            # Divergence kontrolü
            divergence = self._check_rsi_divergence(df)
            
            return {
                'signal': signal,
                'value': round(rsi, 2),
                'previous': round(prev_rsi, 2),
                'status': status,
                'confidence': confidence,
                'divergence': divergence,
                'description': f"RSI: {rsi:.1f} - {status}"
            }
            
        except Exception as e:
            print(f"❌ RSI analiz hatası: {e}")
            return {'signal': 'HOLD', 'value': None, 'status': 'Error'}
    
    def analyze_macd(self, df: pd.DataFrame) -> Dict[str, any]:
        """MACD analizi"""
        try:
            macd_cols = [col for col in df.columns if 'MACD' in col]
            if len(macd_cols) < 2:
                return {'signal': 'HOLD', 'status': 'No data'}
            
            # MACD sütunlarını bul
            macd_line = None
            signal_line = None
            histogram = None
            
            for col in macd_cols:
                if col.endswith('_12_26_9'):
                    macd_line = df[col].iloc[-1]
                elif 'MACDs' in col:
                    signal_line = df[col].iloc[-1]
                elif 'MACDh' in col:
                    histogram = df[col].iloc[-1]
            
            if macd_line is None or signal_line is None:
                return {'signal': 'HOLD', 'status': 'Incomplete data'}
            
            # MACD sinyali
            if macd_line > signal_line and histogram > 0:
                signal = 'LONG'
                status = 'Bullish'
                confidence = 70
            elif macd_line < signal_line and histogram < 0:
                signal = 'SHORT'
                status = 'Bearish'
                confidence = 70
            else:
                signal = 'HOLD'
                status = 'Neutral'
                confidence = 50
            
            # Crossover kontrolü
            if len(df) > 1:
                prev_macd = df[macd_cols[0]].iloc[-2]
                prev_signal = df[[col for col in macd_cols if 'MACDs' in col][0]].iloc[-2] if any('MACDs' in col for col in macd_cols) else signal_line
                
                if prev_macd <= prev_signal and macd_line > signal_line:
                    signal = 'LONG'
                    status = 'Bullish Crossover'
                    confidence = 80
                elif prev_macd >= prev_signal and macd_line < signal_line:
                    signal = 'SHORT'
                    status = 'Bearish Crossover'
                    confidence = 80
            
            return {
                'signal': signal,
                'macd_line': round(macd_line, 6),
                'signal_line': round(signal_line, 6),
                'histogram': round(histogram, 6) if histogram else None,
                'status': status,
                'confidence': confidence,
                'description': f"MACD: {status}"
            }
            
        except Exception as e:
            print(f"❌ MACD analiz hatası: {e}")
            return {'signal': 'HOLD', 'status': 'Error'}
    
    def analyze_bollinger_bands(self, df: pd.DataFrame) -> Dict[str, any]:
        """Bollinger Bands analizi"""
        try:
            bb_cols = [col for col in df.columns if 'BBL' in col or 'BBM' in col or 'BBU' in col]
            if len(bb_cols) < 3:
                return {'signal': 'HOLD', 'status': 'No data'}
            
            current_price = df['close'].iloc[-1]
            
            # Bollinger Bands değerleri
            bb_lower = df[[col for col in bb_cols if 'BBL' in col][0]].iloc[-1]
            bb_middle = df[[col for col in bb_cols if 'BBM' in col][0]].iloc[-1]
            bb_upper = df[[col for col in bb_cols if 'BBU' in col][0]].iloc[-1]
            
            # BB pozisyonu
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            
            # BB sinyali
            if current_price <= bb_lower:
                signal = 'LONG'
                status = 'Oversold (Below Lower Band)'
                confidence = 75
            elif current_price >= bb_upper:
                signal = 'SHORT'
                status = 'Overbought (Above Upper Band)'
                confidence = 75
            elif current_price > bb_middle:
                signal = 'HOLD'
                status = 'Above Middle Band'
                confidence = 55
            else:
                signal = 'HOLD'
                status = 'Below Middle Band'
                confidence = 45
            
            # BB Squeeze kontrolü
            bb_width = (bb_upper - bb_lower) / bb_middle
            squeeze = bb_width < 0.1  # %10'dan dar ise squeeze
            
            return {
                'signal': signal,
                'current_price': round(current_price, 6),
                'lower_band': round(bb_lower, 6),
                'middle_band': round(bb_middle, 6),
                'upper_band': round(bb_upper, 6),
                'position': round(bb_position, 2),
                'width': round(bb_width, 4),
                'squeeze': squeeze,
                'status': status,
                'confidence': confidence,
                'description': f"BB: {status}"
            }
            
        except Exception as e:
            print(f"❌ Bollinger Bands analiz hatası: {e}")
            return {'signal': 'HOLD', 'status': 'Error'}
    
    def analyze_moving_averages(self, df: pd.DataFrame) -> Dict[str, any]:
        """Moving Average analizi"""
        try:
            current_price = df['close'].iloc[-1]
            
            # MA değerleri
            sma20 = df['SMA_20'].iloc[-1] if 'SMA_20' in df.columns else None
            sma50 = df['SMA_50'].iloc[-1] if 'SMA_50' in df.columns else None
            ema20 = df['EMA_20'].iloc[-1] if 'EMA_20' in df.columns else None
            
            signals = []
            
            # SMA 20 sinyali
            if sma20:
                if current_price > sma20:
                    signals.append('LONG')
                else:
                    signals.append('SHORT')
            
            # Golden/Death Cross (SMA20 vs SMA50)
            cross_signal = 'HOLD'
            if sma20 and sma50:
                if sma20 > sma50:
                    cross_signal = 'LONG'
                    cross_status = 'Golden Cross'
                else:
                    cross_signal = 'SHORT'
                    cross_status = 'Death Cross'
                
                signals.append(cross_signal)
            else:
                cross_status = 'No cross data'
            
            # Final MA sinyali
            long_count = signals.count('LONG')
            short_count = signals.count('SHORT')
            
            if long_count > short_count:
                signal = 'LONG'
                confidence = 60 + (long_count * 10)
            elif short_count > long_count:
                signal = 'SHORT'
                confidence = 60 + (short_count * 10)
            else:
                signal = 'HOLD'
                confidence = 50
            
            return {
                'signal': signal,
                'sma20': round(sma20, 6) if sma20 else None,
                'sma50': round(sma50, 6) if sma50 else None,
                'ema20': round(ema20, 6) if ema20 else None,
                'current_price': round(current_price, 6),
                'cross_status': cross_status,
                'confidence': min(90, confidence),
                'description': f"MA: {cross_status}"
            }
            
        except Exception as e:
            print(f"❌ Moving Average analiz hatası: {e}")
            return {'signal': 'HOLD', 'status': 'Error'}
    
    def analyze_stochastic(self, df: pd.DataFrame) -> Dict[str, any]:
        """Stochastic analizi"""
        try:
            stoch_cols = [col for col in df.columns if 'STOCHk' in col or 'STOCHd' in col]
            if len(stoch_cols) < 2:
                return {'signal': 'HOLD', 'status': 'No data'}
            
            stoch_k = df[[col for col in stoch_cols if 'STOCHk' in col][0]].iloc[-1]
            stoch_d = df[[col for col in stoch_cols if 'STOCHd' in col][0]].iloc[-1]
            
            # Stochastic sinyali
            if stoch_k < self.stoch_oversold and stoch_d < self.stoch_oversold:
                signal = 'LONG'
                status = 'Oversold'
                confidence = 70
            elif stoch_k > self.stoch_overbought and stoch_d > self.stoch_overbought:
                signal = 'SHORT'
                status = 'Overbought'
                confidence = 70
            else:
                signal = 'HOLD'
                status = 'Neutral'
                confidence = 50
            
            # Crossover kontrolü
            if len(df) > 1:
                prev_k = df[[col for col in stoch_cols if 'STOCHk' in col][0]].iloc[-2]
                prev_d = df[[col for col in stoch_cols if 'STOCHd' in col][0]].iloc[-2]
                
                if prev_k <= prev_d and stoch_k > stoch_d and stoch_k < 50:
                    signal = 'LONG'
                    status = 'Bullish Crossover'
                    confidence = 75
                elif prev_k >= prev_d and stoch_k < stoch_d and stoch_k > 50:
                    signal = 'SHORT'
                    status = 'Bearish Crossover'
                    confidence = 75
            
            return {
                'signal': signal,
                'stoch_k': round(stoch_k, 2),
                'stoch_d': round(stoch_d, 2),
                'status': status,
                'confidence': confidence,
                'description': f"Stoch: {status}"
            }
            
        except Exception as e:
            print(f"❌ Stochastic analiz hatası: {e}")
            return {'signal': 'HOLD', 'status': 'Error'}
    
    def analyze_volume(self, df: pd.DataFrame) -> Dict[str, any]:
        """Volume analizi"""
        try:
            if 'volume' not in df.columns or len(df) < 20:
                return {'status': 'No volume data'}
            
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Volume sinyali
            if volume_ratio > 1.5:
                status = 'High Volume'
                strength = 'Strong'
            elif volume_ratio > 1.2:
                status = 'Above Average'
                strength = 'Moderate'
            elif volume_ratio < 0.7:
                status = 'Low Volume'
                strength = 'Weak'
            else:
                status = 'Normal Volume'
                strength = 'Normal'
            
            return {
                'current_volume': int(current_volume),
                'average_volume': int(avg_volume),
                'volume_ratio': round(volume_ratio, 2),
                'status': status,
                'strength': strength,
                'description': f"Volume: {status}"
            }
            
        except Exception as e:
            print(f"❌ Volume analiz hatası: {e}")
            return {'status': 'Error'}
    
    def analyze_atr(self, df: pd.DataFrame) -> Dict[str, any]:
        """ATR (Average True Range) analizi"""
        try:
            if 'ATRr_14' not in df.columns:
                return {'status': 'No ATR data'}
            
            atr = df['ATRr_14'].iloc[-1]
            current_price = df['close'].iloc[-1]
            atr_percent = (atr / current_price) * 100
            
            # Volatilite seviyesi
            if atr_percent > 5:
                volatility = 'Very High'
            elif atr_percent > 3:
                volatility = 'High'
            elif atr_percent > 2:
                volatility = 'Moderate'
            elif atr_percent > 1:
                volatility = 'Low'
            else:
                volatility = 'Very Low'
            
            return {
                'atr_value': round(atr, 6),
                'atr_percent': round(atr_percent, 2),
                'volatility': volatility,
                'description': f"Volatilite: {volatility}"
            }
            
        except Exception as e:
            print(f"❌ ATR analiz hatası: {e}")
            return {'status': 'Error'}
    
    def _check_rsi_divergence(self, df: pd.DataFrame) -> Dict[str, any]:
        """RSI divergence kontrolü"""
        try:
            if len(df) < 20 or 'RSI_14' not in df.columns:
                return {'detected': False}
            
            # Son 20 mumda peak ve valley'leri bul
            prices = df['close'].tail(20).values
            rsi_values = df['RSI_14'].tail(20).values
            
            # Basit divergence kontrolü
            price_trend = prices[-1] - prices[0]
            rsi_trend = rsi_values[-1] - rsi_values[0]
            
            # Bullish divergence: Fiyat düşüyor, RSI yükseliyor
            if price_trend < 0 and rsi_trend > 0:
                return {
                    'detected': True,
                    'type': 'bullish',
                    'description': 'Bullish divergence tespit edildi'
                }
            
            # Bearish divergence: Fiyat yükseliyor, RSI düşüyor
            elif price_trend > 0 and rsi_trend < 0:
                return {
                    'detected': True,
                    'type': 'bearish',
                    'description': 'Bearish divergence tespit edildi'
                }
            
            return {'detected': False}
            
        except Exception as e:
            return {'detected': False, 'error': str(e)}
    
    def _calculate_technical_signal(self, signals: List[str], indicators: Dict) -> Tuple[str, int]:
        """Teknik gösterge sinyallerini birleştir"""
        try:
            if not signals:
                return 'HOLD', 50
            
            # Sinyal sayılarını hesapla
            long_count = signals.count('LONG')
            short_count = signals.count('SHORT')
            
            # Ağırlıklı hesaplama
            total_confidence = 0
            signal_weights = {
                'rsi': 1.2,      # RSI daha önemli
                'macd': 1.1,     # MACD önemli
                'bollinger': 1.0, # BB normal
                'moving_averages': 1.1, # MA önemli
                'stochastic': 0.9  # Stoch daha az önemli
            }
            
            weighted_long = 0
            weighted_short = 0
            
            for indicator_name, indicator_data in indicators.items():
                if indicator_data.get('signal') == 'LONG':
                    weight = signal_weights.get(indicator_name, 1.0)
                    confidence = indicator_data.get('confidence', 60)
                    weighted_long += weight * confidence
                elif indicator_data.get('signal') == 'SHORT':
                    weight = signal_weights.get(indicator_name, 1.0)
                    confidence = indicator_data.get('confidence', 60)
                    weighted_short += weight * confidence
            
            # Final sinyal
            if weighted_long > weighted_short:
                final_signal = 'LONG'
                confidence = min(95, int(weighted_long / len([s for s in signals if s == 'LONG']) if long_count > 0 else 60))
            elif weighted_short > weighted_long:
                final_signal = 'SHORT'
                confidence = min(95, int(weighted_short / len([s for s in signals if s == 'SHORT']) if short_count > 0 else 60))
            else:
                final_signal = 'HOLD'
                confidence = 50
            
            return final_signal, confidence
            
        except Exception as e:
            print(f"❌ Teknik sinyal hesaplama hatası: {e}")
            return 'HOLD', 50
    
    def _generate_technical_summary(self, indicators: Dict, signal: str) -> str:
        """Teknik analiz özeti oluştur"""
        try:
            positive_indicators = []
            negative_indicators = []
            
            for name, data in indicators.items():
                if data.get('signal') == 'LONG':
                    positive_indicators.append(name.upper())
                elif data.get('signal') == 'SHORT':
                    negative_indicators.append(name.upper())
            
            summary = f"Teknik analiz sonucu: {signal} sinyali. "
            
            if positive_indicators:
                summary += f"Yükseliş yönünde: {', '.join(positive_indicators)}. "
            
            if negative_indicators:
                summary += f"Düşüş yönünde: {', '.join(negative_indicators)}. "
            
            # Volume durumu
            if 'volume' in indicators:
                volume_status = indicators['volume'].get('status', '')
                if volume_status:
                    summary += f"Hacim durumu: {volume_status}."
            
            return summary
            
        except Exception as e:
            return f"Teknik analiz tamamlandı. {signal} sinyali tespit edildi."

# Singleton instance
technical_analysis_service = TechnicalAnalysisService()

