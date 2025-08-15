import requests
import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import talib

class ChartDataService:
    def __init__(self):
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.binance = ccxt.binance({
            'apiKey': '',  # Boş bırakıyoruz, public data için gerekli değil
            'secret': '',
            'sandbox': False,
            'rateLimit': 1200,
            'enableRateLimit': True,
        })
        
        # Rate limiting için
        self.last_request_time = 0
        self.rate_limit_delay = 1.5
        
        print("📊 Chart Data Service başlatıldı")
    
    def _rate_limit(self):
        """Rate limit kontrolü"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[pd.DataFrame]:
        """
        OHLCV verisi al - önce CoinGecko, sonra Binance
        
        Args:
            symbol: Coin sembolü (BTC, ETH, etc.)
            timeframe: Zaman dilimi (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Kaç mum verisi (max 1000)
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            # Önce CoinGecko'dan deneyelim
            coingecko_data = self._get_coingecko_ohlcv(symbol, timeframe, limit)
            if coingecko_data is not None:
                print(f"✅ {symbol} OHLCV verisi CoinGecko'dan alındı ({len(coingecko_data)} mum)")
                return coingecko_data
            
            # CoinGecko başarısızsa Binance'i deneyelim
            print(f"⚠️ CoinGecko'dan {symbol} verisi alınamadı, Binance deneniyor...")
            binance_data = self._get_binance_ohlcv(symbol, timeframe, limit)
            if binance_data is not None:
                print(f"✅ {symbol} OHLCV verisi Binance'dan alındı ({len(binance_data)} mum)")
                return binance_data
            
            print(f"❌ {symbol} için OHLCV verisi alınamadı")
            return None
            
        except Exception as e:
            print(f"❌ {symbol} OHLCV veri alma hatası: {e}")
            return None
    
    def _get_coingecko_ohlcv(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        """CoinGecko'dan OHLCV verisi al"""
        try:
            self._rate_limit()
            
            # CoinGecko coin ID'sini bul
            coin_id = self._symbol_to_coingecko_id(symbol)
            if not coin_id:
                return None
            
            # Zaman dilimini CoinGecko formatına çevir
            days = self._timeframe_to_days(timeframe, limit)
            
            url = f"{self.coingecko_base_url}/coins/{coin_id}/ohlc"
            params = {
                'vs_currency': 'usd',
                'days': days
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0:
                    # CoinGecko OHLC formatı: [timestamp, open, high, low, close]
                    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
                    df['volume'] = 0  # CoinGecko OHLC'de volume yok
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    
                    # Son limit kadar veri al
                    df = df.tail(limit).reset_index(drop=True)
                    
                    return df
            
            return None
            
        except Exception as e:
            print(f"❌ CoinGecko OHLCV hatası: {e}")
            return None
    
    def _get_binance_ohlcv(self, symbol: str, timeframe: str, limit: int) -> Optional[pd.DataFrame]:
        """Binance'dan OHLCV verisi al"""
        try:
            # Symbol formatını Binance'a uygun hale getir
            binance_symbol = f"{symbol.upper()}USDT"
            
            # Binance timeframe formatı
            binance_timeframe = self._convert_timeframe_to_binance(timeframe)
            
            # OHLCV verisi al
            ohlcv = self.binance.fetch_ohlcv(binance_symbol, binance_timeframe, limit=limit)
            
            if ohlcv and len(ohlcv) > 0:
                # DataFrame'e çevir
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                return df
            
            return None
            
        except Exception as e:
            print(f"❌ Binance OHLCV hatası: {e}")
            return None
    
    def _symbol_to_coingecko_id(self, symbol: str) -> Optional[str]:
        """Symbol'ü CoinGecko ID'sine çevir"""
        symbol_mapping = {
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
            'ALGO': 'algorand',
            'XMR': 'monero',
            'ICP': 'internet-computer',
            'NEAR': 'near',
            'APT': 'aptos',
            'SUI': 'sui',
            'TAO': 'bittensor',
            'HBAR': 'hedera-hashgraph',
            'SHIB': 'shiba-inu',
            'PEPE': 'pepe',
            'BONK': 'bonk',
            'WLD': 'worldcoin-wld',
            'RENDER': 'render-token',
            'FET': 'fetch-ai',
            'PENGU': 'pudgy-penguins',
            'TRUMP': 'maga',
        }
        
        return symbol_mapping.get(symbol.upper())
    
    def _timeframe_to_days(self, timeframe: str, limit: int) -> int:
        """Timeframe ve limit'e göre kaç günlük veri gerektiğini hesapla"""
        timeframe_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
        
        minutes = timeframe_minutes.get(timeframe, 60)
        total_minutes = limit * minutes
        days = max(1, total_minutes // 1440)  # En az 1 gün
        
        return min(days, 365)  # CoinGecko max 365 gün
    
    def _convert_timeframe_to_binance(self, timeframe: str) -> str:
        """Timeframe'i Binance formatına çevir"""
        binance_mapping = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }
        
        return binance_mapping.get(timeframe, '1h')
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Teknik analiz göstergelerini hesapla (TA-Lib kullanarak)
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Teknik göstergeler eklenmiş DataFrame
        """
        try:
            if df is None or len(df) < 20:
                print("❌ Teknik gösterge hesaplama için yeterli veri yok")
                return df
            
            # TA-Lib ile teknik göstergeleri hesapla
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            volume = df['volume'].values
            
            # RSI
            df['RSI_14'] = talib.RSI(close, timeperiod=14)
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            df['MACD_12_26_9'] = macd
            df['MACDs_12_26_9'] = macd_signal
            df['MACDh_12_26_9'] = macd_hist
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            df['BBL_20_2.0'] = bb_lower
            df['BBM_20_2.0'] = bb_middle
            df['BBU_20_2.0'] = bb_upper
            
            # Moving Averages
            df['SMA_20'] = talib.SMA(close, timeperiod=20)
            df['SMA_50'] = talib.SMA(close, timeperiod=50)
            df['EMA_20'] = talib.EMA(close, timeperiod=20)
            
            # ATR
            df['ATRr_14'] = talib.ATR(high, low, close, timeperiod=14)
            
            # Stochastic
            stoch_k, stoch_d = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
            df['STOCHk_14_3_3'] = stoch_k
            df['STOCHd_14_3_3'] = stoch_d
            
            print(f"✅ Teknik göstergeler hesaplandı ({len(df.columns)} sütun)")
            return df
            
        except Exception as e:
            print(f"❌ Teknik gösterge hesaplama hatası: {e}")
            return df
    
    def get_multiple_timeframes(self, symbol: str, timeframes: List[str] = None, limit: int = 100) -> Dict[str, pd.DataFrame]:
        """
        Birden fazla timeframe için veri al
        
        Args:
            symbol: Coin sembolü
            timeframes: Zaman dilimleri listesi
            limit: Her timeframe için kaç mum
            
        Returns:
            Timeframe -> DataFrame mapping
        """
        if timeframes is None:
            timeframes = ['15m', '1h', '4h', '1d']
        
        results = {}
        
        for tf in timeframes:
            try:
                df = self.get_ohlcv_data(symbol, tf, limit)
                if df is not None:
                    # Teknik göstergeleri ekle
                    df = self.calculate_technical_indicators(df)
                    results[tf] = df
                    print(f"✅ {symbol} {tf} verisi hazır")
                else:
                    print(f"❌ {symbol} {tf} verisi alınamadı")
                    
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"❌ {symbol} {tf} veri alma hatası: {e}")
        
        return results
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Son fiyatı al"""
        try:
            # Önce CoinGecko'dan deneyelim
            coin_id = self._symbol_to_coingecko_id(symbol)
            if coin_id:
                self._rate_limit()
                url = f"{self.coingecko_base_url}/simple/price"
                params = {
                    'ids': coin_id,
                    'vs_currencies': 'usd'
                }
                
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if coin_id in data and 'usd' in data[coin_id]:
                        return float(data[coin_id]['usd'])
            
            # CoinGecko başarısızsa Binance'i deneyelim
            binance_symbol = f"{symbol.upper()}USDT"
            ticker = self.binance.fetch_ticker(binance_symbol)
            if ticker and 'last' in ticker:
                return float(ticker['last'])
            
            return None
            
        except Exception as e:
            print(f"❌ {symbol} son fiyat alma hatası: {e}")
            return None

# Singleton instance
chart_data_service = ChartDataService()

