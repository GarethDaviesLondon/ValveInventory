#!/usr/bin/env python3
"""
fetch_datasheets.py - build a local datasheet archive for the types you hold.

This fetches only the types present in valves.db, not the whole site. Frank's
is run on donations, so the defaults here are deliberately slow and sequential.
Run it overnight and leave it alone.

  python3 fetch_datasheets.py --index          # stage 1: map the site
  python3 fetch_datasheets.py --download       # stage 2: pull matching PDFs
  python3 valves.py scan                       # stage 3: link files to types

Stage 1 crawls the /sheets/ tree and caches every PDF href it finds in
url_index.json. Stage 2 downloads only those whose filename matches one of
your types. Both stages are resumable - rerun and they skip what is done.
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import valvelib as V

ROOT = "https://frank.pocnet.net/sheets/"
UA = "valve-inventory/1.0 (personal collection catalogue; polite, rate-limited)"
INDEX_FILE = "url_index.json"


def get(url, delay):
    """Fetch `url` after sleeping `delay` seconds, and return the raw response body.

    The sleep happens before every request (index-page fetches and PDF
    downloads alike) so the crawler and downloader are both rate-limited
    the same way.
    """
    time.sleep(delay)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def crawl(args):
    """Walk the /sheets/ directory listings and record every PDF link."""
    seen_dirs, pdfs = set(), {}
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE) as f:
            cached = json.load(f)
        seen_dirs = set(cached.get("dirs", []))
        pdfs = cached.get("pdfs", {})
        print(f"resuming: {len(seen_dirs)} dirs, {len(pdfs)} pdfs already indexed")

    queue = [ROOT] if not seen_dirs else [d for d in cached.get("queue", []) if d not in seen_dirs]
    if not queue and not seen_dirs:
        # Cache existed but had nothing usable queued (e.g. malformed/empty file) - start over.
        queue = [ROOT]

    try:
        while queue:
            url = queue.pop(0)
            if url in seen_dirs:
                continue
            try:
                body = get(url, args.delay).decode("utf-8", "replace")
            except Exception as e:
                print(f"  skip {url}: {e}")
                seen_dirs.add(url)
                continue
            seen_dirs.add(url)

            for href in re.findall(r'href="([^"]+)"', body):
                href = html.unescape(href)
                # Skip query strings, fragments, and any absolute/external link that
                # isn't itself under ROOT (sort-order links, parent-dir links, ads, etc).
                if href.startswith(("?", "#", "/", "http")) and not href.startswith(ROOT):
                    continue
                full = urllib.parse.urljoin(url, href)
                if not full.startswith(ROOT):
                    continue
                if full.endswith("/"):
                    if full not in seen_dirs and full not in queue:
                        queue.append(full)
                elif full.lower().endswith(".pdf"):
                    # Filenames often carry a "~variant" suffix (e.g. scan source/rev);
                    # strip it so all variants of one type key group under the same stem.
                    stem = V.norm(os.path.splitext(os.path.basename(full))[0].split("~")[0])
                    if stem:
                        pdfs.setdefault(stem, []).append(full)

            if len(seen_dirs) % 25 == 0:
                print(f"  {len(seen_dirs)} dirs, {len(pdfs)} distinct types, {len(queue)} queued")
    except KeyboardInterrupt:
        print("\ninterrupted - progress saved, rerun to continue")

    with open(INDEX_FILE, "w") as f:
        json.dump({"dirs": sorted(seen_dirs), "pdfs": pdfs, "queue": queue}, f)
    print(f"\nindexed {len(pdfs)} distinct types across {len(seen_dirs)} directories")
    print(f"saved to {INDEX_FILE}")


def download(args):
    """Fetch PDFs from url_index.json for every valve type (and equivalent) held in args.db.

    Requires --index to have been run first. Downloads go under
    args.archive/<first-letter-of-key>/, at most args.per_type per type key,
    skipping files already present. Resumable: rerun to pick up where a
    previous run (or --limit cutoff) left off.
    """
    if not os.path.exists(INDEX_FILE):
        print(f"{INDEX_FILE} not found - run with --index first")
        return
    with open(INDEX_FILE) as f:
        pdfs = json.load(f)["pdfs"]

    con = V.connect(args.db)
    wanted = {}
    for r in con.execute("SELECT type_key, name, equivalents FROM valve_type"):
        wanted[r["type_key"]] = r["name"]
        # Equivalents (e.g. a Mullard type sold under a Brimar name) map to the same
        # datasheet demand, so a match on any of them counts as "held".
        for e in (r["equivalents"] or "").split():
            k = V.norm(e)
            if k:
                wanted.setdefault(k, r["name"])

    os.makedirs(args.archive, exist_ok=True)
    hits = [(k, urls) for k, urls in pdfs.items() if k in wanted]
    print(f"{len(hits)} of your {len(wanted)} type designations have a datasheet\n")

    got = skipped = failed = 0
    for key, urls in sorted(hits):
        for url in urls[:args.per_type]:
            name = os.path.basename(urllib.parse.urlparse(url).path)
            sub = os.path.join(args.archive, key[0])
            os.makedirs(sub, exist_ok=True)
            # Prefix the type key onto the filename unless it's already there, so
            # files are identifiable by type even outside their per-letter folder.
            dest = os.path.join(sub, f"{key}~{name}" if not name.upper().startswith(key) else name)
            if os.path.exists(dest) and os.path.getsize(dest) > 0:
                skipped += 1
                continue
            try:
                data = get(url, args.delay)
                with open(dest, "wb") as f:
                    f.write(data)
                got += 1
                print(f"  {key:<12} {len(data)//1024:>5} kB  {name}")
            except Exception as e:
                failed += 1
                print(f"  {key:<12} FAILED  {e}")
            if args.limit and got >= args.limit:
                print(f"\nstopping at --limit {args.limit}")
                print(f"downloaded {got}, already had {skipped}, failed {failed}")
                return

    print(f"\ndownloaded {got}, already had {skipped}, failed {failed}")
    print(f"now run:  python3 valves.py scan --archive {args.archive}")


def main():
    """Parse CLI args and run stage 1 (--index/crawl), stage 2 (--download), or print help."""
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--index", action="store_true", help="stage 1: crawl and map the site")
    p.add_argument("--download", action="store_true", help="stage 2: fetch matching PDFs")
    p.add_argument("--db", default=V.DB_DEFAULT)
    p.add_argument("--archive", default=V.ARCHIVE_DEFAULT)
    p.add_argument("--delay", type=float, default=2.0,
                   help="seconds between requests (default 2.0 - please do not lower)")
    p.add_argument("--per-type", type=int, default=2,
                   help="max datasheets to keep per type (default 2)")
    p.add_argument("--limit", type=int, default=0, help="stop after N downloads (0 = no limit)")
    a = p.parse_args()

    if a.index:
        crawl(a)
    elif a.download:
        download(a)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
