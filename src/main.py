import argparse
from local_environment import get_local_environments
from settings import DEFAULT_R_CUT


def main():
    args = parse_args()
    get_local_environments(args.mol_file, args.r_cut)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("mol_file")
    parser.add_argument(
        "--r_cut", type=int, default=DEFAULT_R_CUT, help="integer radius of cutting"
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
