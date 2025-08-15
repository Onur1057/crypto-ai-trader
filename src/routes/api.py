from flask import Blueprint, jsonify, request
from src.services.signal_generator import signal_generator
from src.services.coin_gecko_service import coin_gecko_service
from src.services.coin_filter_service import coin_filter_service
import threading
import time

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global değişkenler
auto_scan_active = False
auto_scan_thread = None
scan_count = 0
last_scan_time = None

def auto_scan_worker():
    """Otomatik tarama worker fonksiyonu"""
    global scan_count, last_scan_time
    
    while auto_scan_active:
        try:
            print("🔍 Otomatik tarama başlatılıyor...")
            
            # Sinyal üret
            new_signals = signal_generator.generate_signals()
            
            # Fiyat güncellemesi - DÜZELTİLDİ
            active_signals = signal_generator.get_active_signals()
            if active_signals:
                # Coin sembollerini topla (coin_id yerine)
                symbols = [s.get('coin_symbol', s.get('symbol', '')) for s in active_signals if s.get('coin_symbol') or s.get('symbol')]
                
                if symbols:
                    price_updates = coin_gecko_service.get_current_prices(symbols)
                    
                    # Manuel PnL güncelleme
                    updated_count = 0
                    for signal in active_signals:
                        symbol = signal.get('coin_symbol', signal.get('symbol', '')).lower()
                        if symbol in price_updates:
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
                                    
                                    # USD PnL hesaplama
                                    position_size = 1000
                                    pnl_usd = (pnl_percentage / 100) * position_size
                                    signal['pnl_usd'] = round(pnl_usd, 2)
                                    
                                    updated_count += 1
                    
                    if updated_count > 0:
                        signal_generator.save_signals()
                        print(f"💰 {updated_count} sinyal PnL güncellendi")
            
            scan_count += 1
            last_scan_time = time.time()
            
            print(f"✅ Otomatik tarama tamamlandı: {len(new_signals)} yeni sinyal")
            
            # 5 dakika bekle (300 saniye)
            for _ in range(300):
                if not auto_scan_active:
                    break
                time.sleep(1)
                
        except Exception as e:
            print(f"❌ Otomatik tarama hatası: {e}")
            time.sleep(60)  # Hata durumunda 1 dakika bekle

@api_bp.route('/signals', methods=['GET'])
def get_signals():
    """Aktif sinyalleri döner"""
    try:
        signals = signal_generator.get_active_signals()
        return jsonify({
            'success': True,
            'signals': signals,
            'count': len(signals)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/signals/history', methods=['GET'])
def get_signal_history():
    """Sinyal geçmişini döner"""
    try:
        history = signal_generator.get_signal_history()
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/signals/stats', methods=['GET'])
def get_signal_stats():
    """Sinyal performans istatistiklerini döner - YENİ ENDPOINT"""
    try:
        stats = signal_generator.get_performance_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/signals/generate', methods=['POST'])
def generate_signals():
    """Manuel sinyal üretimi"""
    try:
        data = request.get_json() or {}
        max_signals = data.get('max_signals', 15)
        
        new_signals = signal_generator.generate_signals(max_signals)
        
        return jsonify({
            'success': True,
            'signals': new_signals,
            'count': len(new_signals)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/signals/update-prices', methods=['POST'])
def update_signal_prices():
    """Sinyal fiyatlarını güncelle"""
    try:
        active_signals = signal_generator.get_active_signals()
        if not active_signals:
            return jsonify({
                'success': True,
                'message': 'Aktif sinyal yok',
                'updated_count': 0
            })
        
        # Coin sembollerini topla (coin_id yerine coin_symbol kullan)
        symbols = [s.get('coin_symbol', s.get('symbol', '')) for s in active_signals if s.get('coin_symbol') or s.get('symbol')]
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'Sinyallerde coin_symbol bulunamadı'
            }), 400
        
        # CoinGecko'dan fiyatları al
        price_updates = coin_gecko_service.get_current_prices(symbols)
        
        if not price_updates:
            return jsonify({
                'success': False,
                'error': 'Fiyat verisi alınamadı'
            }), 500
        
        # Sinyalleri güncelle
        updated_count = 0
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
                        
                        updated_count += 1
        
        # Güncellenmiş sinyalleri kaydet
        signal_generator.save_signals()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'price_updates': price_updates,
            'message': f'{updated_count} sinyal güncellendi'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/auto-scan/start', methods=['POST'])
def start_auto_scan():
    """Otomatik taramayı başlat"""
    global auto_scan_active, auto_scan_thread
    
    try:
        if auto_scan_active:
            return jsonify({
                'success': False,
                'message': 'Otomatik tarama zaten aktif'
            })
        
        auto_scan_active = True
        auto_scan_thread = threading.Thread(target=auto_scan_worker, daemon=True)
        auto_scan_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Otomatik tarama başlatıldı'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/auto-scan/stop', methods=['POST'])
def stop_auto_scan():
    """Otomatik taramayı durdur"""
    global auto_scan_active
    
    try:
        auto_scan_active = False
        
        return jsonify({
            'success': True,
            'message': 'Otomatik tarama durduruldu'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/auto-scan/status', methods=['GET'])
def get_auto_scan_status():
    """Otomatik tarama durumunu döner"""
    try:
        return jsonify({
            'success': True,
            'active': auto_scan_active,
            'scan_count': scan_count,
            'last_scan_time': last_scan_time
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/coins', methods=['GET'])
def get_coins():
    """Coin listesi döner"""
    try:
        limit = request.args.get('limit', 100, type=int)
        coins = coin_gecko_service.get_coins(limit)
        
        return jsonify({
            'success': True,
            'coins': coins,
            'count': len(coins)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/coins/filtered', methods=['GET'])
def get_filtered_coins():
    """Filtrelenmiş coin listesi döner"""
    try:
        limit = request.args.get('limit', 100, type=int)
        all_coins = coin_gecko_service.get_coins(limit)
        filtered_coins = coin_filter_service.filter_coins_for_trading(all_coins)
        
        return jsonify({
            'success': True,
            'all_coins_count': len(all_coins),
            'filtered_coins_count': len(filtered_coins),
            'filtered_coins': filtered_coins,
            'filter_criteria': coin_filter_service.get_filter_criteria()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Sağlık kontrolü"""
    try:
        stats = signal_generator.get_performance_stats()
        
        return jsonify({
            'success': True,
            'message': 'Crypto AI Backend çalışıyor',
            'auto_scan_active': auto_scan_active,
            'scan_count': scan_count,
            'active_signals': stats['active_signals'],
            'closed_signals': stats['closed_signals'],
            'total_signals': stats['total_signals'],
            'success_rate': f"{stats['success_rate']:.1f}%",
            'total_pnl': f"${stats['total_pnl_usd']:.2f}"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/clear-data', methods=['POST'])
def clear_all_data():
    """Tüm sinyal verilerini temizle"""
    try:
        result = signal_generator.clear_all_data()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'cleared_active_signals': result['cleared_active'],
                'cleared_history_signals': result['cleared_history'],
                'timestamp': time.time()
            })
        else:
            return jsonify({
                'success': False,
                'error': result['message']
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/reset-system', methods=['POST'])
def reset_system():
    """Sistemi tamamen sıfırla"""
    try:
        global scan_count, last_scan_time
        
        # Verileri temizle
        result = signal_generator.clear_all_data()
        
        # Tarama sayacını sıfırla
        scan_count = 0
        last_scan_time = None
        
        return jsonify({
            'success': True,
            'message': 'Sistem tamamen sıfırlandı',
            'cleared_active_signals': result['cleared_active'],
            'cleared_history_signals': result['cleared_history'],
            'scan_count_reset': True,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



# Chat API Endpoints
@api_bp.route('/chat/message', methods=['POST'])
def chat_message():
    """AI Chat mesajı gönder"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Mesaj boş olamaz'
            }), 400
        
        # Basit AI yanıtları (gerçek AI entegrasyonu için OpenAI API kullanılabilir)
        ai_responses = {
            'merhaba': 'Merhaba! Size nasıl yardımcı olabilirim?',
            'yardım': 'Trading konularında size yardımcı olabilirim. Risk yönetimi, teknik analiz, pattern tanıma gibi konularda sorularınızı sorabilirsiniz.',
            'risk': 'Risk yönetimi trading\'in en önemli parçasıdır. Her işlemde maksimum %2-3 risk almalısınız.',
            'analiz': 'Teknik analiz için support/resistance seviyelerini, RSI, MACD gibi indikatörleri takip etmelisiniz.',
            'pattern': 'Chart pattern\'leri trend değişimlerini öngörmede çok faydalıdır. Head & Shoulders, Double Top/Bottom gibi pattern\'leri öğrenmelisiniz.',
            'stop': 'Stop-loss her pozisyonda mutlaka kullanılmalıdır. Risk/reward oranınız en az 1:2 olmalıdır.',
            'default': 'Bu konuda size yardımcı olabilirim. Daha spesifik sorular sorabilir misiniz?'
        }
        
        # Basit keyword matching
        response = ai_responses.get('default')
        user_lower = user_message.lower()
        
        for keyword, ai_response in ai_responses.items():
            if keyword in user_lower:
                response = ai_response
                break
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/chat/history', methods=['GET'])
def chat_history():
    """Chat geçmişini getir"""
    try:
        # Basit chat geçmişi (gerçek uygulamada veritabanından gelir)
        history = [
            {
                'id': 1,
                'message': 'Merhaba! Ben AI Trading Asistanınızım.',
                'sender': 'ai',
                'timestamp': time.time() - 3600
            }
        ]
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Training API Endpoints
@api_bp.route('/training/add-pattern', methods=['POST'])
def add_training_pattern():
    """Eğitim pattern'i ekle"""
    try:
        data = request.get_json()
        
        required_fields = ['pattern_type', 'coin_pair', 'timeframe', 'result', 'market_condition']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} alanı gerekli'
                }), 400
        
        # Eğitim verisini kaydet (gerçek uygulamada veritabanına kaydedilir)
        training_data = {
            'id': int(time.time()),
            'pattern_type': data['pattern_type'],
            'coin_pair': data['coin_pair'],
            'timeframe': data['timeframe'],
            'result': data['result'],
            'market_condition': data['market_condition'],
            'price_data': data.get('price_data', ''),
            'notes': data.get('notes', ''),
            'created_at': time.time()
        }
        
        return jsonify({
            'success': True,
            'message': 'Eğitim verisi başarıyla eklendi',
            'training_id': training_data['id']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/training/stats', methods=['GET'])
def training_stats():
    """Eğitim istatistiklerini getir"""
    try:
        # Basit eğitim istatistikleri (gerçek uygulamada veritabanından gelir)
        stats = {
            'total_trainings': 0,
            'successful_patterns': 0,
            'learning_rate': 0.0,
            'different_coins': 0,
            'recent_trainings': []
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/training/patterns', methods=['GET'])
def get_training_patterns():
    """Eğitim pattern'lerini listele"""
    try:
        # Basit pattern listesi (gerçek uygulamada veritabanından gelir)
        patterns = []
        
        return jsonify({
            'success': True,
            'patterns': patterns
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Learning API Endpoints
@api_bp.route('/learning/add-link', methods=['POST'])
def add_learning_link():
    """Öğrenme linki ekle"""
    try:
        data = request.get_json()
        
        url = data.get('url', '').strip()
        description = data.get('description', '').strip()
        
        if not url or not description:
            return jsonify({
                'success': False,
                'error': 'URL ve açıklama gerekli'
            }), 400
        
        # Link verisini kaydet (gerçek uygulamada veritabanına kaydedilir)
        link_data = {
            'id': int(time.time()),
            'url': url,
            'description': description,
            'created_at': time.time()
        }
        
        return jsonify({
            'success': True,
            'message': 'Öğrenme linki başarıyla eklendi',
            'link_id': link_data['id']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/learning/upload-pdf', methods=['POST'])
def upload_learning_pdf():
    """PDF dosyası yükle"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Dosya seçilmedi'
            }), 400
        
        file = request.files['file']
        topic = request.form.get('topic', '').strip()
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Dosya seçilmedi'
            }), 400
        
        if not topic:
            return jsonify({
                'success': False,
                'error': 'Konu başlığı gerekli'
            }), 400
        
        # PDF dosyasını kaydet (gerçek uygulamada dosya sistemi veya cloud storage)
        filename = f"learning_{int(time.time())}_{file.filename}"
        
        return jsonify({
            'success': True,
            'message': 'PDF başarıyla yüklendi',
            'filename': filename,
            'topic': topic
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/learning/stats', methods=['GET'])
def learning_stats():
    """Öğrenme istatistiklerini getir"""
    try:
        # Basit öğrenme istatistikleri (gerçek uygulamada veritabanından gelir)
        stats = {
            'total_interactions': 0,
            'learned_topics': 0,
            'success_rate': 0.0,
            'active_days': 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/stats/detailed', methods=['GET'])
def get_detailed_stats():
    """Detaylı istatistikler API endpoint'i"""
    try:
        signals = signal_generator.get_active_signals()
        
        if not signals:
            return jsonify({
                'success': True,
                'stats': {
                    'overview': {
                        'total_pnl': 0,
                        'active_signals': 0,
                        'success_rate': 0,
                        'avg_confidence': 0
                    },
                    'top_performers': [],
                    'worst_performers': [],
                    'confidence_analysis': {
                        'high': {'count': 0, 'avg_pnl': 0, 'signals': []},
                        'medium': {'count': 0, 'avg_pnl': 0, 'signals': []},
                        'low': {'count': 0, 'avg_pnl': 0, 'signals': []}
                    },
                    'sector_analysis': {
                        'layer1': [],
                        'meme': [],
                        'defi': [],
                        'ai': []
                    },
                    'risk_analysis': {
                        'high_risk': [],
                        'profit_opportunities': []
                    }
                }
            })
        
        # Genel istatistikler
        total_pnl = sum(s.get('pnl_usd', 0) for s in signals)
        profitable_count = len([s for s in signals if s.get('pnl_percentage', 0) > 0])
        success_rate = (profitable_count / len(signals)) * 100 if signals else 0
        avg_confidence = sum(s.get('confidence', 0) for s in signals) / len(signals) if signals else 0
        
        # En iyi ve en kötü performanslar
        sorted_by_pnl = sorted(signals, key=lambda x: x.get('pnl_percentage', 0), reverse=True)
        top_performers = sorted_by_pnl[:5]
        worst_performers = sorted_by_pnl[-5:]
        
        # Güven seviyesi analizi
        high_confidence = [s for s in signals if s.get('confidence', 0) >= 90]
        medium_confidence = [s for s in signals if 80 <= s.get('confidence', 0) < 90]
        low_confidence = [s for s in signals if s.get('confidence', 0) < 80]
        
        confidence_analysis = {
            'high': {
                'count': len(high_confidence),
                'avg_pnl': sum(s.get('pnl_percentage', 0) for s in high_confidence) / len(high_confidence) if high_confidence else 0,
                'signals': [{'symbol': s['coin_symbol'], 'pnl': s.get('pnl_percentage', 0), 'confidence': s.get('confidence', 0)} for s in high_confidence]
            },
            'medium': {
                'count': len(medium_confidence),
                'avg_pnl': sum(s.get('pnl_percentage', 0) for s in medium_confidence) / len(medium_confidence) if medium_confidence else 0,
                'signals': [{'symbol': s['coin_symbol'], 'pnl': s.get('pnl_percentage', 0), 'confidence': s.get('confidence', 0)} for s in medium_confidence]
            },
            'low': {
                'count': len(low_confidence),
                'avg_pnl': sum(s.get('pnl_percentage', 0) for s in low_confidence) / len(low_confidence) if low_confidence else 0,
                'signals': [{'symbol': s['coin_symbol'], 'pnl': s.get('pnl_percentage', 0), 'confidence': s.get('confidence', 0)} for s in low_confidence]
            }
        }
        
        # Sektör analizi
        layer1_coins = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOT', 'DOGE', 'AVAX', 'MATIC']
        meme_coins = ['PEPE', 'BONK', 'SHIB', 'FLOKI', 'WIF', 'PENGU', 'DOGE']
        defi_coins = ['UNI', 'AAVE', 'MKR', 'COMP', 'YFI', 'SUSHI', 'SNX', 'CRV']
        ai_coins = ['TAO', 'RENDER', 'FET', 'AGIX']
        
        def categorize_signals(coin_list):
            return [s for s in signals if s['coin_symbol'] in coin_list]
        
        sector_analysis = {
            'layer1': categorize_signals(layer1_coins),
            'meme': categorize_signals(meme_coins),
            'defi': categorize_signals(defi_coins),
            'ai': categorize_signals(ai_coins)
        }
        
        # Risk analizi
        high_risk_signals = []
        profit_opportunities = []
        
        for signal in signals:
            pnl_pct = signal.get('pnl_percentage', 0)
            current_price = signal.get('current_price', 0)
            sl_level = signal.get('sl_level', 0)
            tp_levels = signal.get('tp_levels', {})
            
            # Yüksek risk: Stop-loss'a yakın pozisyonlar
            if sl_level and current_price:
                if signal['direction'] == 'LONG':
                    risk_ratio = (current_price - sl_level) / current_price
                else:
                    risk_ratio = (sl_level - current_price) / current_price
                
                if risk_ratio < 0.05:  # %5'ten az mesafe
                    high_risk_signals.append(signal)
            
            # Kar fırsatları: TP'ye yakın pozisyonlar
            if tp_levels and current_price:
                tp1 = tp_levels.get('tp1', 0)
                if tp1:
                    if signal['direction'] == 'LONG':
                        tp_ratio = (tp1 - current_price) / current_price
                    else:
                        tp_ratio = (current_price - tp1) / current_price
                    
                    if tp_ratio < 0.02:  # %2'den az mesafe
                        profit_opportunities.append(signal)
        
        return jsonify({
            'success': True,
            'stats': {
                'overview': {
                    'total_pnl': total_pnl,
                    'active_signals': len(signals),
                    'success_rate': success_rate,
                    'avg_confidence': avg_confidence
                },
                'top_performers': top_performers,
                'worst_performers': worst_performers,
                'confidence_analysis': confidence_analysis,
                'sector_analysis': sector_analysis,
                'risk_analysis': {
                    'high_risk': high_risk_signals,
                    'profit_opportunities': profit_opportunities
                }
            }
        })
        
    except Exception as e:
        print(f"❌ Detaylı istatistik hatası: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/api/stats/export', methods=['GET'])
def export_stats():
    """İstatistikleri CSV formatında export et"""
    try:
        signals = signal_generator.get_active_signals()
        
        if not signals:
            return jsonify({'success': False, 'error': 'Aktif sinyal bulunamadı'}), 404
        
        # CSV formatında veri hazırla
        csv_data = []
        csv_data.append(['Coin', 'Direction', 'Entry_Price', 'Current_Price', 'PnL_Percentage', 'PnL_USD', 'Confidence', 'Status', 'Timestamp'])
        
        for signal in signals:
            csv_data.append([
                signal['coin_symbol'],
                signal['direction'],
                signal['entry_price'],
                signal.get('current_price', 0),
                signal.get('pnl_percentage', 0),
                signal.get('pnl_usd', 0),
                signal.get('confidence', 0),
                signal.get('status', 'Aktif'),
                signal.get('timestamp', '')
            ])
        
        return jsonify({
            'success': True,
            'csv_data': csv_data,
            'filename': f'crypto_ai_signals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        print(f"❌ Export hatası: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

