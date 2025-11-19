from waitress import serve
from app_new import create_app

app = create_app()

# Настройка количества потоков и порта
serve(app, host='0.0.0.0', port=5000, threads=16)

