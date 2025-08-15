import requests
import time
from typing import List, Dict, Any, Optional

class CoinGeckoService:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.last_request_time = 0
        self.rate_limit_delay = 1.2  # 1.2 saniye bekleme (rate limit için)
        
    def _rate_limit(self):
        """Rate limit kontrolü"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """API isteği yap"""
        try:
            self._rate_limit()
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ CoinGecko API hatası: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ CoinGecko istek hatası: {e}")
            return None
    
    def get_coins(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Coin listesi al"""
        try:
            print(f"🔍 CoinGecko'dan {limit} coin alınıyor...")
            
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h'
            }
            
            data = self._make_request('coins/markets', params)
            
            if data:
                print(f"✅ {len(data)} coin verisi alındı")
                return data
            else:
                print("❌ Coin verisi alınamadı")
                return []
                
        except Exception as e:
            print(f"❌ get_coins hatası: {e}")
            return []
    
    def get_coin_prices(self, coin_ids: List[str]) -> Dict[str, float]:
        """Belirli coinlerin fiyatlarını al"""
        try:
            if not coin_ids:
                return {}
            
            # CoinGecko API limiti nedeniyle 100'er coin grupla
            all_prices = {}
            chunk_size = 100
            
            for i in range(0, len(coin_ids), chunk_size):
                chunk = coin_ids[i:i + chunk_size]
                ids_str = ','.join(chunk)
                
                print(f"🚀 {len(chunk)} coin için fiyatlar alınıyor...")
                
                params = {
                    'ids': ids_str,
                    'vs_currencies': 'usd'
                }
                
                data = self._make_request('simple/price', params)
                
                if data:
                    for coin_id, price_data in data.items():
                        if 'usd' in price_data:
                            all_prices[coin_id] = price_data['usd']
                
                # Rate limit için bekleme
                if i + chunk_size < len(coin_ids):
                    time.sleep(1)
            
            print(f"✅ {len(all_prices)} coin fiyatı alındı")
            return all_prices
            
        except Exception as e:
            print(f"❌ get_coin_prices hatası: {e}")
            return {}
    
    def get_top_coins(self, limit: int = 100) -> List[Dict[str, Any]]:
        """En popüler coinleri al (get_coins ile aynı)"""
        return self.get_coins(limit=limit)
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Symbol listesine göre güncel fiyatları al"""
        try:
            if not symbols:
                return {}
            
            # Sembolleri coin ID'lerine çevir (basit mapping)
            symbol_to_id = {
                'btc': 'bitcoin',
                'eth': 'ethereum',
                'bnb': 'binancecoin',
                'ada': 'cardano',
                'sol': 'solana',
                'xrp': 'ripple',
                'dot': 'polkadot',
                'doge': 'dogecoin',
                'avax': 'avalanche-2',
                'matic': 'matic-network',
                'link': 'chainlink',
                'uni': 'uniswap',
                'ltc': 'litecoin',
                'bch': 'bitcoin-cash',
                'xlm': 'stellar',
                'vet': 'vechain',
                'fil': 'filecoin',
                'trx': 'tron',
                'etc': 'ethereum-classic',
                'atom': 'cosmos',
                'cro': 'crypto-com-chain',
                'algo': 'algorand',
                'mana': 'decentraland',
                'sand': 'the-sandbox',
                'axs': 'axie-infinity',
                'theta': 'theta-token',
                'icp': 'internet-computer',
                'flow': 'flow',
                'egld': 'elrond-erd-2',
                'xtz': 'tezos',
                'aave': 'aave',
                'mkr': 'maker',
                'comp': 'compound-governance-token',
                'yfi': 'yearn-finance',
                'sushi': 'sushi',
                'snx': 'havven',
                'crv': 'curve-dao-token',
                'bal': 'balancer',
                'ren': 'republic-protocol',
                'zrx': '0x',
                'omg': 'omisego',
                'bat': 'basic-attention-token',
                'zil': 'zilliqa',
                'enj': 'enjincoin',
                'hot': 'holo',
                'icx': 'icon',
                'qtum': 'qtum',
                'ont': 'ontology',
                'zec': 'zcash',
                'dash': 'dash',
                'xmr': 'monero',
                'dcr': 'decred',
                'lsk': 'lisk',
                'nano': 'nano',
                'dgb': 'digibyte',
                'rvn': 'ravencoin',
                'sc': 'siacoin',
                'dent': 'dent',
                'storj': 'storj',
                'ankr': 'ankr',
                'celr': 'celer-network',
                'coti': 'coti',
                'ctsi': 'cartesi',
                'band': 'band-protocol',
                'ocean': 'ocean-protocol',
                'nkn': 'nkn',
                'iotx': 'iotex',
                'fet': 'fetch-ai',
                'agix': 'singularitynet',
                'render': 'render-token',
                'tao': 'bittensor',
                'pepe': 'pepe',
                'bonk': 'bonk',
                'shib': 'shiba-inu',
                'floki': 'floki',
                'wif': 'dogwifcoin',
                'pengu': 'pudgy-penguins',  # DÜZELTİLDİ: pengu -> pudgy-penguins
                'spx': 'spx6900',
                'trump': 'maga',
                'pnut': 'peanut-the-squirrel',
                'goat': 'goatseus-maximus',
                'act': 'achain',
                'neiro': 'neiro-ethereum',
                'popcat': 'popcat',
                'fartcoin': 'fartcoin',
                'ai16z': 'ai16z',
                'virtual': 'virtual-protocol',
                'zerebro': 'zerebro',
                'griffain': 'griffain',
                'moodeng': 'moo-deng',
                'chillguy': 'just-a-chill-guy',
                'pups': 'bitcoin-puppets',
                'runes': 'runes',
                'ordi': 'ordinals'
            }
            
            coin_ids = []
            for symbol in symbols:
                symbol_lower = symbol.lower()
                if symbol_lower in symbol_to_id:
                    coin_ids.append(symbol_to_id[symbol_lower])
                else:
                    # Basit tahmin: symbol'ü coin id olarak kullan
                    coin_ids.append(symbol_lower)
            
            prices_by_id = self.get_coin_prices(coin_ids)
            
            # Sonuçları symbol bazında döndür
            result = {}
            for i, symbol in enumerate(symbols):
                coin_id = coin_ids[i] if i < len(coin_ids) else symbol.lower()
                if coin_id in prices_by_id:
                    result[symbol.lower()] = prices_by_id[coin_id]
            
            return result
            
        except Exception as e:
            print(f"❌ get_current_prices hatası: {e}")
            return {}

    def get_coin_details(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Coin detaylarını al"""
        try:
            print(f"🔍 {coin_id} detayları alınıyor...")
            
            data = self._make_request(f'coins/{coin_id}')
            
            if data:
                print(f"✅ {coin_id} detayları alındı")
                return data
            else:
                print(f"❌ {coin_id} detayları alınamadı")
                return None
                
        except Exception as e:
            print(f"❌ get_coin_details hatası: {e}")
            return None

# Singleton instance
coin_gecko_service = CoinGeckoService()

