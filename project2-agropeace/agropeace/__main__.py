"""Command-line entry point.

    python -m agropeace -c demo/demo_config.json run        # dashboard + APIs
    python -m agropeace -c demo/demo_config.json risk       # print community risk table
    python -m agropeace -c demo/demo_config.json audit      # verify the audit chain
"""

import argparse
import sys

from .engine import Engine, load_config, master_key_from_env


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="agropeace")
    ap.add_argument("-c", "--config", default="config.json")
    ap.add_argument("cmd", choices=["run", "risk", "audit"])
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    eng = Engine(cfg, master_key_from_env(cfg))
    if args.cmd == "run":
        from .server import serve
        serve(eng, cfg["dashboard"]["host"], cfg["dashboard"]["port"])
    elif args.cmd == "risk":
        print(f"{'Community':<22}{'LGA':<11}{'Level':<10}{'Score':>6}  Main drivers")
        for c in eng.community:
            print(f"{c['community']:<22}{c['lga']:<11}{c['level']:<10}{c['score']:>6.2f}  {', '.join(c['drivers'])}")
    elif args.cmd == "audit":
        for e in reversed(eng.audit.recent(30)):
            print(f"{e['ts'][:19]}  {e['actor']:<16} {e['action']}")
        print("chain:", eng.audit.verify())
    return 0


if __name__ == "__main__":
    sys.exit(main())
