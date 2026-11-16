"""Start the Billbo prototype.   python run.py   then open http://127.0.0.1:8000
Options:  --port 8000   --reset (reload the demo data)"""
import argparse

from billbo import db, server

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Billbo prototype server")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--reset", action="store_true", help="reload the demo data before starting")
    args = ap.parse_args()
    if args.reset:
        db.reset()
    server.serve(args.port)
