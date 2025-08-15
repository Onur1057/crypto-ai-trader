#!/usr/bin/env python3
"""
WSGI Entry Point for Crypto AI Trader
Production deployment için gunicorn ile kullanılır
"""

import os
import sys

# Proje dizinini Python path'e ekle
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Ana uygulamayı import et
from src.main import app

if __name__ == "__main__":
    # Development modunda çalıştırma
    app.run(host='0.0.0.0', port=5000, debug=False)
else:
    # Production modunda gunicorn tarafından kullanılır
    application = app

