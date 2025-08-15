import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.signal import find_peaks, argrelextrema
import warnings
warnings.filterwarnings('ignore')

class PatternRecognitionService:
    def __init__(self):
        self.min_pattern_length = 20  # Minimum pattern uzunluğu
        self.peak_distance = 5  # Peak'ler arası minimum mesafe
        self.tolerance = 0.02  # %2 tolerans
        
        print("🎯 Pattern Recognition Service başlatıldı")
    
    def analyze_patterns(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Tüm pattern'leri analiz et
        
        Args:
            df: OHLCV + teknik göstergeler DataFrame
            
        Returns:
            Pattern analiz sonuçları
        """
        try:
            if df is None or len(df) < self.min_pattern_length:
                return {'patterns': [], 'signal': 'HOLD', 'confidence': 0}
            
            patterns = []
            signals = []
            
            # 1. Double Top/Bottom
            double_top = self.detect_double_top(df)
            if double_top['detected']:
                patterns.append(double_top)
                signals.append(double_top['signal'])
            
            double_bottom = self.detect_double_bottom(df)
            if double_bottom['detected']:
                patterns.append(double_bottom)
                signals.append(double_bottom['signal'])
            
            # 2. Head and Shoulders
            head_shoulders = self.detect_head_and_shoulders(df)
            if head_shoulders['detected']:
                patterns.append(head_shoulders)
                signals.append(head_shoulders['signal'])
            
            # 3. Triangle Patterns
            triangle = self.detect_triangle_patterns(df)
            if triangle['detected']:
                patterns.append(triangle)
                signals.append(triangle['signal'])
            
            # 4. Support/Resistance
            support_resistance = self.detect_support_resistance(df)
            patterns.append(support_resistance)
            
            # 5. Trend Analysis
            trend = self.analyze_trend(df)
            patterns.append(trend)
            
            # Final signal ve confidence hesapla
            final_signal, confidence = self._calculate_final_signal(signals, df)
            
            return {
                'patterns': patterns,
                'signal': final_signal,
                'confidence': confidence,
                'analysis': self._generate_analysis_text(patterns, final_signal)
            }
            
        except Exception as e:
            print(f"❌ Pattern analiz hatası: {e}")
            return {'patterns': [], 'signal': 'HOLD', 'confidence': 0}
    
    def detect_double_top(self, df: pd.DataFrame) -> Dict[str, any]:
        """İkili Tepe (Double Top) pattern tespiti"""
        try:
            highs = df['high'].values
            
            # Peak'leri bul
            peaks, _ = find_peaks(highs, distance=self.peak_distance, prominence=np.std(highs) * 0.5)
            
            if len(peaks) < 2:
                return {'detected': False, 'pattern': 'double_top'}
            
            # Son iki peak'i kontrol et
            for i in range(len(peaks) - 1):
                peak1_idx = peaks[i]
                peak2_idx = peaks[i + 1]
                
                peak1_price = highs[peak1_idx]
                peak2_price = highs[peak2_idx]
                
                # İki peak'in yüksekliği benzer mi?
                price_diff = abs(peak1_price - peak2_price) / peak1_price
                
                if price_diff <= self.tolerance:
                    # Aradaki valley'i bul
                    valley_start = peak1_idx
                    valley_end = peak2_idx
                    valley_idx = valley_start + np.argmin(highs[valley_start:valley_end])
                    valley_price = highs[valley_idx]
                    
                    # Valley, peak'lerden en az %3 düşük olmalı
                    valley_drop = (peak1_price - valley_price) / peak1_price
                    
                    if valley_drop >= 0.03:
                        return {
                            'detected': True,
                            'pattern': 'double_top',
                            'signal': 'SHORT',
                            'confidence': min(90, 60 + valley_drop * 100),
                            'peak1_idx': peak1_idx,
                            'peak2_idx': peak2_idx,
                            'valley_idx': valley_idx,
                            'resistance_level': (peak1_price + peak2_price) / 2,
                            'target': valley_price,
                            'description': f"İkili tepe formasyonu tespit edildi. Direnç: ${(peak1_price + peak2_price) / 2:.4f}"
                        }
            
            return {'detected': False, 'pattern': 'double_top'}
            
        except Exception as e:
            print(f"❌ Double top tespit hatası: {e}")
            return {'detected': False, 'pattern': 'double_top'}
    
    def detect_double_bottom(self, df: pd.DataFrame) -> Dict[str, any]:
        """İkili Dip (Double Bottom) pattern tespiti"""
        try:
            lows = df['low'].values
            
            # Valley'leri bul (negatif peak'ler)
            valleys, _ = find_peaks(-lows, distance=self.peak_distance, prominence=np.std(lows) * 0.5)
            
            if len(valleys) < 2:
                return {'detected': False, 'pattern': 'double_bottom'}
            
            # Son iki valley'i kontrol et
            for i in range(len(valleys) - 1):
                valley1_idx = valleys[i]
                valley2_idx = valleys[i + 1]
                
                valley1_price = lows[valley1_idx]
                valley2_price = lows[valley2_idx]
                
                # İki valley'in derinliği benzer mi?
                price_diff = abs(valley1_price - valley2_price) / valley1_price
                
                if price_diff <= self.tolerance:
                    # Aradaki peak'i bul
                    peak_start = valley1_idx
                    peak_end = valley2_idx
                    peak_idx = peak_start + np.argmax(lows[peak_start:peak_end])
                    peak_price = lows[peak_idx]
                    
                    # Peak, valley'lerden en az %3 yüksek olmalı
                    peak_rise = (peak_price - valley1_price) / valley1_price
                    
                    if peak_rise >= 0.03:
                        return {
                            'detected': True,
                            'pattern': 'double_bottom',
                            'signal': 'LONG',
                            'confidence': min(90, 60 + peak_rise * 100),
                            'valley1_idx': valley1_idx,
                            'valley2_idx': valley2_idx,
                            'peak_idx': peak_idx,
                            'support_level': (valley1_price + valley2_price) / 2,
                            'target': peak_price,
                            'description': f"İkili dip formasyonu tespit edildi. Destek: ${(valley1_price + valley2_price) / 2:.4f}"
                        }
            
            return {'detected': False, 'pattern': 'double_bottom'}
            
        except Exception as e:
            print(f"❌ Double bottom tespit hatası: {e}")
            return {'detected': False, 'pattern': 'double_bottom'}
    
    def detect_head_and_shoulders(self, df: pd.DataFrame) -> Dict[str, any]:
        """Baş-Omuz (Head and Shoulders) pattern tespiti"""
        try:
            highs = df['high'].values
            
            # Peak'leri bul
            peaks, _ = find_peaks(highs, distance=self.peak_distance, prominence=np.std(highs) * 0.3)
            
            if len(peaks) < 3:
                return {'detected': False, 'pattern': 'head_and_shoulders'}
            
            # Son 3 peak'i kontrol et
            for i in range(len(peaks) - 2):
                left_shoulder_idx = peaks[i]
                head_idx = peaks[i + 1]
                right_shoulder_idx = peaks[i + 2]
                
                left_shoulder = highs[left_shoulder_idx]
                head = highs[head_idx]
                right_shoulder = highs[right_shoulder_idx]
                
                # Head, shoulder'lardan yüksek olmalı
                if head > left_shoulder and head > right_shoulder:
                    # Shoulder'lar benzer yükseklikte olmalı
                    shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
                    
                    if shoulder_diff <= self.tolerance * 2:  # Daha toleranslı
                        # Head, shoulder'lardan en az %5 yüksek olmalı
                        head_prominence = (head - max(left_shoulder, right_shoulder)) / max(left_shoulder, right_shoulder)
                        
                        if head_prominence >= 0.05:
                            # Neckline hesapla (iki valley arasındaki çizgi)
                            valley1_start = left_shoulder_idx
                            valley1_end = head_idx
                            valley1_idx = valley1_start + np.argmin(highs[valley1_start:valley1_end])
                            
                            valley2_start = head_idx
                            valley2_end = right_shoulder_idx
                            valley2_idx = valley2_start + np.argmin(highs[valley2_start:valley2_end])
                            
                            neckline = (highs[valley1_idx] + highs[valley2_idx]) / 2
                            
                            return {
                                'detected': True,
                                'pattern': 'head_and_shoulders',
                                'signal': 'SHORT',
                                'confidence': min(95, 70 + head_prominence * 100),
                                'left_shoulder_idx': left_shoulder_idx,
                                'head_idx': head_idx,
                                'right_shoulder_idx': right_shoulder_idx,
                                'neckline': neckline,
                                'target': neckline - (head - neckline),  # Target = neckline - head height
                                'description': f"Baş-omuz formasyonu tespit edildi. Boyun çizgisi: ${neckline:.4f}"
                            }
            
            return {'detected': False, 'pattern': 'head_and_shoulders'}
            
        except Exception as e:
            print(f"❌ Head and shoulders tespit hatası: {e}")
            return {'detected': False, 'pattern': 'head_and_shoulders'}
    
    def detect_triangle_patterns(self, df: pd.DataFrame) -> Dict[str, any]:
        """Üçgen formasyonları tespiti"""
        try:
            if len(df) < 30:
                return {'detected': False, 'pattern': 'triangle'}
            
            highs = df['high'].values
            lows = df['low'].values
            
            # Son 30 mum için trend çizgileri hesapla
            recent_data = df.tail(30)
            
            # Yüksek noktaların trendi
            high_peaks, _ = find_peaks(recent_data['high'].values, distance=3)
            low_valleys, _ = find_peaks(-recent_data['low'].values, distance=3)
            
            if len(high_peaks) >= 2 and len(low_valleys) >= 2:
                # Üst trend çizgisi (resistance)
                high_slope = self._calculate_trendline_slope(high_peaks, recent_data['high'].values)
                
                # Alt trend çizgisi (support)
                low_slope = self._calculate_trendline_slope(low_valleys, recent_data['low'].values)
                
                # Üçgen türünü belirle
                if abs(high_slope) < 0.001 and low_slope > 0.001:
                    # Ascending Triangle
                    return {
                        'detected': True,
                        'pattern': 'ascending_triangle',
                        'signal': 'LONG',
                        'confidence': 75,
                        'description': "Yükselen üçgen formasyonu - yükseliş sinyali"
                    }
                elif high_slope < -0.001 and abs(low_slope) < 0.001:
                    # Descending Triangle
                    return {
                        'detected': True,
                        'pattern': 'descending_triangle',
                        'signal': 'SHORT',
                        'confidence': 75,
                        'description': "Alçalan üçgen formasyonu - düşüş sinyali"
                    }
                elif high_slope < -0.001 and low_slope > 0.001:
                    # Symmetrical Triangle
                    return {
                        'detected': True,
                        'pattern': 'symmetrical_triangle',
                        'signal': 'HOLD',
                        'confidence': 60,
                        'description': "Simetrik üçgen formasyonu - kırılım bekleniyor"
                    }
            
            return {'detected': False, 'pattern': 'triangle'}
            
        except Exception as e:
            print(f"❌ Triangle pattern tespit hatası: {e}")
            return {'detected': False, 'pattern': 'triangle'}
    
    def detect_support_resistance(self, df: pd.DataFrame) -> Dict[str, any]:
        """Destek ve direnç seviyelerini tespit et"""
        try:
            if len(df) < 20:
                return {'pattern': 'support_resistance', 'levels': []}
            
            highs = df['high'].values
            lows = df['low'].values
            closes = df['close'].values
            current_price = closes[-1]
            
            # Peak ve valley'leri bul
            peaks, _ = find_peaks(highs, distance=5, prominence=np.std(highs) * 0.3)
            valleys, _ = find_peaks(-lows, distance=5, prominence=np.std(lows) * 0.3)
            
            resistance_levels = []
            support_levels = []
            
            # Resistance levels (peaks)
            for peak_idx in peaks:
                level = highs[peak_idx]
                # Bu seviyeye yakın başka peak'ler var mı?
                nearby_peaks = [highs[p] for p in peaks if abs(highs[p] - level) / level <= 0.01]
                if len(nearby_peaks) >= 2:  # En az 2 kez test edilmiş
                    resistance_levels.append({
                        'level': level,
                        'type': 'resistance',
                        'strength': len(nearby_peaks),
                        'distance_pct': (level - current_price) / current_price * 100
                    })
            
            # Support levels (valleys)
            for valley_idx in valleys:
                level = lows[valley_idx]
                # Bu seviyeye yakın başka valley'ler var mı?
                nearby_valleys = [lows[v] for v in valleys if abs(lows[v] - level) / level <= 0.01]
                if len(nearby_valleys) >= 2:  # En az 2 kez test edilmiş
                    support_levels.append({
                        'level': level,
                        'type': 'support',
                        'strength': len(nearby_valleys),
                        'distance_pct': (current_price - level) / level * 100
                    })
            
            # En yakın destek ve direnci bul
            nearest_resistance = None
            nearest_support = None
            
            if resistance_levels:
                nearest_resistance = min(resistance_levels, key=lambda x: abs(x['distance_pct']))
            
            if support_levels:
                nearest_support = min(support_levels, key=lambda x: abs(x['distance_pct']))
            
            return {
                'pattern': 'support_resistance',
                'resistance_levels': resistance_levels,
                'support_levels': support_levels,
                'nearest_resistance': nearest_resistance,
                'nearest_support': nearest_support,
                'current_price': current_price
            }
            
        except Exception as e:
            print(f"❌ Support/Resistance tespit hatası: {e}")
            return {'pattern': 'support_resistance', 'levels': []}
    
    def analyze_trend(self, df: pd.DataFrame) -> Dict[str, any]:
        """Trend analizi"""
        try:
            if len(df) < 20:
                return {'pattern': 'trend', 'direction': 'SIDEWAYS'}
            
            # Moving average'ları kullan
            if 'SMA_20' in df.columns and 'SMA_50' in df.columns:
                sma20 = df['SMA_20'].iloc[-1]
                sma50 = df['SMA_50'].iloc[-1]
                current_price = df['close'].iloc[-1]
                
                # Trend yönünü belirle
                if current_price > sma20 > sma50:
                    trend = 'UPTREND'
                    strength = min(95, ((current_price - sma50) / sma50) * 100 + 60)
                elif current_price < sma20 < sma50:
                    trend = 'DOWNTREND'
                    strength = min(95, ((sma50 - current_price) / current_price) * 100 + 60)
                else:
                    trend = 'SIDEWAYS'
                    strength = 50
                
                return {
                    'pattern': 'trend',
                    'direction': trend,
                    'strength': strength,
                    'sma20': sma20,
                    'sma50': sma50,
                    'current_price': current_price
                }
            
            # MA yoksa basit trend hesapla
            recent_closes = df['close'].tail(10).values
            if recent_closes[-1] > recent_closes[0]:
                return {'pattern': 'trend', 'direction': 'UPTREND', 'strength': 60}
            elif recent_closes[-1] < recent_closes[0]:
                return {'pattern': 'trend', 'direction': 'DOWNTREND', 'strength': 60}
            else:
                return {'pattern': 'trend', 'direction': 'SIDEWAYS', 'strength': 50}
                
        except Exception as e:
            print(f"❌ Trend analiz hatası: {e}")
            return {'pattern': 'trend', 'direction': 'SIDEWAYS'}
    
    def _calculate_trendline_slope(self, indices: np.ndarray, values: np.ndarray) -> float:
        """Trend çizgisinin eğimini hesapla"""
        if len(indices) < 2:
            return 0
        
        x = indices
        y = values[indices]
        
        # Linear regression
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def _calculate_final_signal(self, signals: List[str], df: pd.DataFrame) -> Tuple[str, int]:
        """Tüm pattern sinyallerini birleştirip final sinyal hesapla"""
        try:
            if not signals:
                return 'HOLD', 50
            
            # Sinyal sayılarını hesapla
            long_count = signals.count('LONG')
            short_count = signals.count('SHORT')
            hold_count = signals.count('HOLD')
            
            # RSI ile onay
            rsi_signal = 'HOLD'
            rsi_confidence_bonus = 0
            
            if 'RSI_14' in df.columns:
                rsi = df['RSI_14'].iloc[-1]
                if rsi < 30:
                    rsi_signal = 'LONG'
                    rsi_confidence_bonus = 10
                elif rsi > 70:
                    rsi_signal = 'SHORT'
                    rsi_confidence_bonus = 10
            
            # Final sinyal
            if long_count > short_count and long_count > hold_count:
                final_signal = 'LONG'
                confidence = min(95, 60 + (long_count * 10) + rsi_confidence_bonus)
            elif short_count > long_count and short_count > hold_count:
                final_signal = 'SHORT'
                confidence = min(95, 60 + (short_count * 10) + rsi_confidence_bonus)
            else:
                final_signal = 'HOLD'
                confidence = 50
            
            # RSI ile uyumlu ise confidence artır
            if final_signal == rsi_signal:
                confidence = min(95, confidence + 5)
            
            return final_signal, int(confidence)
            
        except Exception as e:
            print(f"❌ Final sinyal hesaplama hatası: {e}")
            return 'HOLD', 50
    
    def _generate_analysis_text(self, patterns: List[Dict], signal: str) -> str:
        """Analiz metnini oluştur"""
        try:
            detected_patterns = [p for p in patterns if p.get('detected', False)]
            
            if not detected_patterns:
                return f"Teknik analiz sonucunda {signal} sinyali tespit edildi. Mevcut piyasa koşullarında dikkatli yaklaşım önerilir."
            
            pattern_names = []
            for pattern in detected_patterns:
                if pattern['pattern'] == 'double_top':
                    pattern_names.append("ikili tepe formasyonu")
                elif pattern['pattern'] == 'double_bottom':
                    pattern_names.append("ikili dip formasyonu")
                elif pattern['pattern'] == 'head_and_shoulders':
                    pattern_names.append("baş-omuz formasyonu")
                elif 'triangle' in pattern['pattern']:
                    pattern_names.append("üçgen formasyonu")
            
            if pattern_names:
                patterns_text = ", ".join(pattern_names)
                return f"Teknik analizde {patterns_text} tespit edildi. Bu formasyonlar {signal} yönünde sinyal veriyor."
            else:
                return f"Kapsamlı teknik analiz sonucunda {signal} sinyali oluştu. Trend ve momentum göstergeleri bu yönü destekliyor."
                
        except Exception as e:
            return f"Teknik analiz tamamlandı. {signal} sinyali tespit edildi."

# Singleton instance
pattern_recognition_service = PatternRecognitionService()

