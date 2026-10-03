#!/usr/bin/env python3
import argparse
from pathlib import Path
import zipfile


def add_if(zf, path, arcname=None):
    if not path:
        return
    p = Path(path)
    if p.exists() and p.is_file():
        zf.write(p, arcname or p.name)


def main():
    ap = argparse.ArgumentParser(description='Build a Plottr review ZIP. The original .pltr is excluded unless --include-original is set.')
    ap.add_argument('--output', required=True)
    ap.add_argument('--proposal')
    ap.add_argument('--comparison')
    ap.add_argument('--review-md')
    ap.add_argument('--review-html')
    ap.add_argument('--validation')
    ap.add_argument('--manifest')
    ap.add_argument('--original')
    ap.add_argument('--include-original', action='store_true')
    args = ap.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        add_if(zf, args.proposal)
        add_if(zf, args.comparison)
        add_if(zf, args.review_md)
        add_if(zf, args.review_html)
        add_if(zf, args.validation)
        add_if(zf, args.manifest)
        if args.include_original:
            if not args.original:
                raise SystemExit('--include-original requires --original')
            add_if(zf, args.original)

    print(out)


if __name__ == '__main__':
    main()
