import os

from waitress import serve
from app_new import create_app

app = create_app()

port = int(os.environ.get("PORT", 5000))
serve(app, host="0.0.0.0", port=port, threads=16)

