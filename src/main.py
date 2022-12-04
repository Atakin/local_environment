import argparse
from src.local_environment import get_local_environments


def main():
    args = parse_args()
    get_local_environments(args.mol_file)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mol_file")
    return parser.parse_args()


if __name__ == "__main__":
    main()
