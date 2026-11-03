#!/usr/bin/env python3
"""Unipi kernel config fragment tooling.

The input to every command is an explicit, ordered list of Kconfig fragment
files. The product -> fragment mapping lives in ``configs/products/*.mk`` and is
resolved by the Makefile; this tool knows nothing about products.

Subcommands:
    gen    <frag>...   merge fragments into linux/.config
    report <frag>...   show what an edited .config contains that fragments don't
    check  <frag>...   validate fragments (duplicates, non-landing values)
    where  CONFIG_X    show which fragment defines a symbol
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CONFIGS_DIR = Path(__file__).resolve().parent
ROOT = CONFIGS_DIR.parent
LINUX = ROOT / "linux"
DEFAULT_FRAGDIR = CONFIGS_DIR / "fragments"

SYM = r"CONFIG_[A-Za-z0-9_]+"
CONFIG_LINE_RE = re.compile(rf"^({SYM})=(.*)$")
NOTSET_RE = re.compile(rf"^# ({SYM}) is not set$")


def err(msg: str) -> None:
    print(f"configtool: {msg}", file=sys.stderr)


def die(msg: str) -> None:
    err(msg)
    sys.exit(1)


def require_tree() -> None:
    if not (LINUX / "scripts" / "kconfig" / "merge_config.sh").is_file():
        die("linux/ is not prepared (run ./prepare.sh build)")


def match_config_line(line: str):
    """Return (symbol, value) for a config or 'is not set' line, else None."""
    m = CONFIG_LINE_RE.match(line) or NOTSET_RE.match(line)
    if not m:
        return None
    return m.group(1), ("n" if line.startswith("#") else m.group(2))


def parse_file(path: Path) -> dict[str, str]:
    cfg: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        m = match_config_line(raw.strip())
        if m:
            cfg[m[0]] = m[1]
    return cfg


def fragment_symbols(paths) -> dict[str, tuple[Path, int, str]]:
    """symbol -> (file, lineno, value) for every fragment."""
    where: dict[str, tuple[Path, int, str]] = {}
    for p in paths:
        path = Path(p)
        if not path.is_file():
            die(f"fragment not found: {p}")
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            m = match_config_line(raw.strip())
            if m:
                where[m[0]] = (path, lineno, m[1])
    return where


def run(cmd, env) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(LINUX), env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def merge(frags, arch: str, kconfig_config: Path):
    """Merge fragments and resolve defaults into kconfig_config.

    Returns (ok, combined_output). Uses merge_config.sh -m followed by
    olddefconfig — the sequence the fragment split was verified with.
    """
    env = os.environ.copy()
    env["ARCH"] = arch
    env["KCONFIG_CONFIG"] = str(kconfig_config.resolve())
    kconfig_config.parent.mkdir(parents=True, exist_ok=True)
    mc = str(LINUX / "scripts" / "kconfig" / "merge_config.sh")
    p = run([mc, "-m", "-y", *[str(Path(f).resolve()) for f in frags]], env)
    out = p.stdout + p.stderr
    if p.returncode != 0:
        return False, out
    p2 = run(["make", "olddefconfig"], env)
    return p2.returncode == 0, out + p2.stdout + p2.stderr


def resolve_copy(src: Path, dst: Path, arch: str):
    """olddefconfig a copy of src into dst; returns (ok, output)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(src), str(dst))
    env = os.environ.copy()
    env["ARCH"] = arch
    env["KCONFIG_CONFIG"] = str(dst.resolve())
    p = run(["make", "olddefconfig"], env)
    return p.returncode == 0, p.stdout + p.stderr


# --- gen -------------------------------------------------------------------

def cmd_gen(a) -> int:
    require_tree()
    dst = Path(a.config) if a.config else LINUX / ".config"
    ok, out = merge(a.fragments, a.arch, dst)
    if out.strip():
        print(out.strip(), file=sys.stderr)
    if not ok:
        err("fragment merge failed")
        return 1
    return 0


# --- report ----------------------------------------------------------------

def cmd_report(a) -> int:
    require_tree()
    inspected = Path(a.config) if a.config else LINUX / ".config"
    if not inspected.is_file():
        die(f"no config to inspect: {inspected}")

    tmp = Path(tempfile.mkdtemp(prefix="configtool."))
    ok, out = merge(a.fragments, a.arch, tmp / "fragments" / ".config")
    if not ok:
        die("fragment merge failed:\n" + out)
    frags_cfg = parse_file(tmp / "fragments" / ".config")

    ok, out = resolve_copy(inspected, tmp / "inspected" / ".config", a.arch)
    if not ok:
        die("could not resolve the inspected config:\n" + out)
    cur_cfg = parse_file(tmp / "inspected" / ".config")

    where = fragment_symbols(a.fragments)

    def ann(sym: str) -> str:
        w = where.get(sym)
        return f"  [{w[0].name}:{w[1]}]" if w else ""

    added = {s for s in cur_cfg if s not in frags_cfg}
    removed = sorted(s for s in frags_cfg if s not in cur_cfg)
    changed_all = sorted(s for s in frags_cfg if s in cur_cfg
                         and frags_cfg[s] != cur_cfg[s])
    # Only fragment-defined symbols count as "value changes"; anything the
    # fragments don't mention is unrepresented, whether it was absent (n) or
    # merely switched on from its default.
    new_syms = sorted(added | {s for s in changed_all if s not in where})
    val_changes = [s for s in changed_all if s in where]

    if new_syms:
        print("Not represented by any fragment "
              "(add these to a fragment):")
        for s in new_syms:
            print(f"  {s}={cur_cfg[s]}")
    if removed:
        print("Stale fragment lines (in a fragment, absent from the "
              "inspected config):")
        for s in removed:
            print(f"  {s}={frags_cfg[s]}{ann(s)}")
    if val_changes:
        print("Value changes in fragment-defined symbols "
              "(fragments -> inspected):")
        for s in val_changes:
            print(f"  {s}: {frags_cfg[s]} -> {cur_cfg[s]}{ann(s)}")

    if not (new_syms or removed or val_changes):
        print("clean: the inspected config matches the fragments")
    else:
        print(f"\n{len(new_syms)} not represented, {len(removed)} stale, "
              f"{len(val_changes)} changed")
        if a.exit_code:
            return 1
    return 0


# --- check -----------------------------------------------------------------

def cmd_check(a) -> int:
    require_tree()
    problems: list[str] = []

    # 1. conflicting definitions across fragments. A later
    # fragment overriding an earlier "is not set" with =y/=m is allowed.
    seen: dict[str, list[tuple[Path, str]]] = {}
    for p in a.fragments:
        path = Path(p)
        if not path.is_file():
            die(f"fragment not found: {p}")
        for sym, val in parse_file(path).items():
            seen.setdefault(sym, []).append((path, val))
    for sym, defs in sorted(seen.items()):
        enabling = [(p, v) for p, v in defs if v != "n"]
        if len(enabling) > 1:
            where = ", ".join(f"{p.name}={v}" for p, v in defs)
            problems.append(
                f"{sym} enabled in multiple fragments ({where}) - "
                f"only one fragment may enable it")

    # 2. merge and look for values that did not land
    tmp = Path(tempfile.mkdtemp(prefix="configtool."))
    ok, out = merge(a.fragments, a.arch, tmp / ".config")
    if not ok:
        problems.append("fragment merge failed:\n" + out)
    for line in out.splitlines():
        if "Value requested for" in line:
            problems.append("value did not land: " + line)

    if problems:
        print(f"check FAILED ({len(problems)} problem(s)):", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        return 1
    print(f"check ok ({len(a.fragments)} fragments, {len(seen)} symbols)")
    return 0


# --- where -----------------------------------------------------------------

def cmd_where(a) -> int:
    fragdir = Path(a.fragdir)
    if not fragdir.is_dir():
        die(f"fragment directory not found: {fragdir}")
    hits = []
    for path in sorted(fragdir.glob("*.config")):
        for lineno, raw in enumerate(path.read_text().splitlines(), 1):
            m = match_config_line(raw.strip())
            if m and m[0] == a.symbol:
                hits.append((path, lineno, raw.strip()))
    if not hits:
        print(f"{a.symbol}: not defined in any fragment")
        return 0
    for path, lineno, line in hits:
        print(f"{path}:{lineno}: {line}")
    if len(hits) > 1:
        err(f"warning: {a.symbol} is defined in {len(hits)} fragments "
            "(sets should be disjoint)")
    return 0


# --- CLI -------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="configtool.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("gen", help="merge fragments into a .config")
    gen.add_argument("--arch", default="arm64")
    gen.add_argument("--config", help="output config (default linux/.config)")
    gen.add_argument("fragments", nargs="+")
    gen.set_defaults(func=cmd_gen)

    rep = sub.add_parser("report", help="show config vs fragment differences")
    rep.add_argument("--arch", default="arm64")
    rep.add_argument("--config", help="config to inspect (default linux/.config)")
    rep.add_argument("--exit-code", action="store_true",
                     help="exit non-zero when there are differences")
    rep.add_argument("fragments", nargs="+")
    rep.set_defaults(func=cmd_report)

    chk = sub.add_parser("check", help="validate fragments")
    chk.add_argument("--arch", default="arm64")
    chk.add_argument("fragments", nargs="+")
    chk.set_defaults(func=cmd_check)

    wh = sub.add_parser("where", help="locate a symbol in the fragments")
    wh.add_argument("symbol")
    wh.add_argument("--fragdir", default=str(DEFAULT_FRAGDIR))
    wh.set_defaults(func=cmd_where)

    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
