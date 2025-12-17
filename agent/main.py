"""Minimal agent.main to respond to --help for validation."""
import argparse

def main():
    parser = argparse.ArgumentParser(prog='agent.main')
    parser.add_argument('--version', action='store_true', help='Show version')
    args = parser.parse_args()
    if args.version:
        print('agent 0.0')

if __name__ == '__main__':
    main()
