import os
import sys
from app import app

def run_app():
    print(" Starting Medical Chatbot Application") 
    try:
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        print(f"🌐 Server will start on: http://localhost:{port}")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug
        )
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)


def main():

    run_app()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n Shutting down")
        sys.exit(0)
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        sys.exit(1)

