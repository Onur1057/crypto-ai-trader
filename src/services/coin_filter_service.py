from typing import List, Dict, Any, Optional

class CoinFilterService:
    def __init__(self):
        # Hariç tutulacak coin'ler (stablecoin'ler ve düşük volatilite)
        self.excluded_symbols = [
            # Stablecoin'ler
            'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'USDP', 'FRAX', 'LUSD', 'USDD',
            'FDUSD', 'PYUSD', 'CRVUSD', 'GUSD', 'USDK', 'EURS', 'EURT', 'XSGD',
            
            # Wrapped Token'lar (düşük volatilite)
            'WBTC', 'WETH', 'STETH', 'WSTETH', 'RETH', 'CBETH', 'WBETH', 'WEETH',
            'SFRXETH', 'FRXETH', 'ANKR', 'BETH', 'ROCKETPOOL',
            
            # Diğer düşük volatilite coinler
            'PAXG', 'XAUT', 'DGX', 'CACHE', 'PMGT', 'AABBG'
        ]

        # Hariç tutulacak coin ID'leri (CoinGecko ID'leri)
        self.excluded_ids = [
            # Stablecoin ID'leri
            'tether', 'usd-coin', 'binance-usd', 'dai', 'true-usd', 'paxos-standard',
            'frax', 'liquity-usd', 'usdd', 'first-digital-usd', 'paypal-usd',
            'curve-dao-token', 'gemini-dollar', 'usdk', 'stasis-eurs', 'tether-eurt',
            
            # Wrapped Token ID'leri
            'wrapped-bitcoin', 'weth', 'staked-ether', 'wrapped-steth', 'rocket-pool-eth',
            'coinbase-wrapped-staked-eth', 'wrapped-beacon-eth', 'wrapped-eeth',
            'staked-frax-ether', 'frax-ether',
            
            # Altın destekli tokenlar
            'pax-gold', 'tether-gold', 'digix-gold-token', 'cache-gold', 'perth-mint-gold-token'
        ]

        # Minimum volatilite eşiği (24 saatlik fiyat değişimi)
        self.min_volatility_threshold = 0.5  # %0.5

        # Minimum market cap eşiği (USD)
        self.min_market_cap = 10_000_000  # 10 milyon USD

        # Maksimum market cap eşiği (çok büyük coinleri hariç tut)
        self.max_market_cap = 100_000_000_000  # 100 milyar USD

        # Minimum volume eşiği
        self.min_volume = 1_000_000  # 1 milyon USD

    def filter_coins_for_trading(self, coins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Coin listesini filtreler - sadece trading için uygun coinleri döner"""
        print(f"🔍 {len(coins)} coin filtreleniyor...")
        
        filtered_coins = []
        
        for coin in coins:
            # Symbol kontrolü
            symbol = coin.get('symbol', '').upper()
            if symbol in self.excluded_symbols:
                print(f"❌ {symbol} - Hariç tutulan symbol")
                continue

            # ID kontrolü
            coin_id = coin.get('id', '').lower()
            if coin_id in self.excluded_ids:
                print(f"❌ {symbol} - Hariç tutulan ID")
                continue

            # Volatilite kontrolü
            price_change = abs(coin.get('price_change_percentage_24h', 0) or 0)
            if price_change < self.min_volatility_threshold:
                print(f"❌ {symbol} - Düşük volatilite: {price_change:.2f}%")
                continue

            # Market cap kontrolü
            market_cap = coin.get('market_cap')
            if market_cap:
                if market_cap < self.min_market_cap:
                    print(f"❌ {symbol} - Düşük market cap: ${market_cap / 1_000_000:.1f}M")
                    continue

                if market_cap > self.max_market_cap:
                    print(f"❌ {symbol} - Çok yüksek market cap: ${market_cap / 1_000_000_000:.1f}B")
                    continue

            # Volume kontrolü (24 saatlik işlem hacmi)
            total_volume = coin.get('total_volume')
            if total_volume and total_volume < self.min_volume:
                print(f"❌ {symbol} - Düşük volume: ${total_volume / 1_000_000:.1f}M")
                continue

            market_cap_str = f"${market_cap / 1_000_000:.0f}M" if market_cap else "?"
            print(f"✅ {symbol} - Trading için uygun (Vol: {price_change:.2f}%, MC: {market_cap_str})")
            filtered_coins.append(coin)

        print(f"✅ Filtreleme tamamlandı: {len(filtered_coins)}/{len(coins)} coin trading için uygun")
        
        # Volatiliteye göre sırala (en volatil olanlar önce)
        sorted_coins = sorted(filtered_coins, key=lambda x: abs(x.get('price_change_percentage_24h', 0) or 0), reverse=True)

        if len(sorted_coins) >= 10:
            top_10 = sorted_coins[:10]
            top_10_str = ', '.join([f"{c.get('symbol', '').upper()}({abs(c.get('price_change_percentage_24h', 0) or 0):.1f}%)" for c in top_10])
            print(f"📊 En volatil 10 coin: {top_10_str}")

        return sorted_coins

    def is_coin_suitable_for_trading(self, coin: Dict[str, Any]) -> bool:
        """Belirli bir coin'in trading için uygun olup olmadığını kontrol eder"""
        # Symbol kontrolü
        symbol = coin.get('symbol', '').upper()
        if symbol in self.excluded_symbols:
            return False

        # ID kontrolü
        coin_id = coin.get('id', '').lower()
        if coin_id in self.excluded_ids:
            return False

        # Volatilite kontrolü
        price_change = abs(coin.get('price_change_percentage_24h', 0) or 0)
        if price_change < self.min_volatility_threshold:
            return False

        # Market cap kontrolü
        market_cap = coin.get('market_cap')
        if market_cap:
            if market_cap < self.min_market_cap or market_cap > self.max_market_cap:
                return False

        # Volume kontrolü
        total_volume = coin.get('total_volume')
        if total_volume and total_volume < self.min_volume:
            return False

        return True

    def get_excluded_symbols(self) -> List[str]:
        """Hariç tutulan coin listesini döner"""
        return self.excluded_symbols.copy()

    def get_filter_criteria(self) -> Dict[str, Any]:
        """Filtreleme kriterlerini döner"""
        return {
            'min_volatility': self.min_volatility_threshold,
            'min_market_cap': self.min_market_cap,
            'max_market_cap': self.max_market_cap,
            'min_volume': self.min_volume,
            'excluded_symbols': len(self.excluded_symbols),
            'excluded_ids': len(self.excluded_ids)
        }

    def get_filtered_coins(self, limit: int = 50) -> List[Dict[str, Any]]:
        """CoinGecko'dan coin listesi alıp filtreler"""
        try:
            from src.services.coin_gecko_service import CoinGeckoService
            
            coin_gecko = CoinGeckoService()
            
            # CoinGecko'dan coin listesi al
            all_coins = coin_gecko.get_top_coins(limit=limit * 2)  # Daha fazla coin al ki filtrelemeden sonra yeterli kalsın
            
            if not all_coins:
                print("❌ CoinGecko'dan coin verisi alınamadı")
                return []
            
            # Coinleri filtrele
            filtered_coins = self.filter_coins_for_trading(all_coins)
            
            # Limit kadar döndür
            return filtered_coins[:limit]
            
        except Exception as e:
            print(f"❌ get_filtered_coins hatası: {e}")
            return []

    def get_exclusion_reason(self, coin: Dict[str, Any]) -> Optional[str]:
        """Coin'in neden hariç tutulduğunu açıklar"""
        symbol = coin.get('symbol', '').upper()
        coin_id = coin.get('id', '').lower()
        
        if symbol in self.excluded_symbols:
            return f"Hariç tutulan symbol: {symbol}"

        if coin_id in self.excluded_ids:
            return f"Hariç tutulan ID: {coin_id}"

        price_change = abs(coin.get('price_change_percentage_24h', 0) or 0)
        if price_change < self.min_volatility_threshold:
            return f"Düşük volatilite: {price_change:.2f}% (min: {self.min_volatility_threshold}%)"

        market_cap = coin.get('market_cap')
        if market_cap:
            if market_cap < self.min_market_cap:
                return f"Düşük market cap: ${market_cap / 1_000_000:.1f}M (min: ${self.min_market_cap / 1_000_000}M)"

            if market_cap > self.max_market_cap:
                return f"Çok yüksek market cap: ${market_cap / 1_000_000_000:.1f}B (max: ${self.max_market_cap / 1_000_000_000}B)"

        total_volume = coin.get('total_volume')
        if total_volume and total_volume < self.min_volume:
            return f"Düşük volume: ${total_volume / 1_000_000:.1f}M (min: $1M)"

        return None  # Hariç tutulma sebebi yok

# Singleton instance
coin_filter_service = CoinFilterService()

