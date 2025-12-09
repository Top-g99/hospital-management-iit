from typing import Optional
from app import create_app
import os

if __name__ == '__main__':
    flask_application = create_app()
    
    server_port: int = int(os.environ.get('PORT', 5000))
    server_host: str = '127.0.0.1'
    debug_mode: bool = True
    
    flask_application.run(
        host=server_host,
        port=server_port,
        debug=debug_mode
    )
