"""Parse verification before importing application or initializing video."""
import argparse
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description='Toktogi Pico2D candidate')
    parser.add_argument('--verify',action='store_true',help='CPU-only acceptance checks')
    parser.add_argument('--profile',choices=('legacy','seamless'),default='seamless')
    args=parser.parse_args()
    if args.verify:
        from verify_all import verify
        verify()
    else:
        from app import App
        App(native=True,profile=args.profile).run()

if __name__=='__main__':
    try:main()
    except Exception as error:
        raise SystemExit(f'Toktogi failed: {type(error).__name__}: {error}') from error
