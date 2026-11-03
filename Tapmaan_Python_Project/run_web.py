"""Run from the project folder: python run_web.py"""
import argparse
from backend.server import create_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tapmaan local Python website")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = create_server(args.port)
    print(f"Tapmaan is running at http://127.0.0.1:{args.port}")
    print("Keep this window open. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
