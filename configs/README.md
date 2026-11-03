# Kernel config fragments

`linux/.config` is assembled at build time from ordered fragments in
`fragments/`. Fragments are the source of truth; no defconfig is committed.

Merge order is the order in the product map (`products/<product>.mk`, which sets
`<product>_ARCH` and `<product>_Fragments`); later fragments override earlier.

- `00-arm64` `05-core` `10-storage` `15-net` `30-usb` `35-peripherals` — common
  (arch/CPU, base services + crypto + security, storage/fs, networking, USB,
  peripherals)
- `50-soc-*` — per-SoC; `60-board-*` and `90-override*` — reserved

A symbol should be *enabled* in exactly one fragment, meaning that it is possible to
enable a symbol which a lower level fragment specifically disables (`# CONFIG_X not set`).
`#` comments document provenance and are ignored by the merge.

## Merge

    make unipi-<product>_defconfig      # = configtool.py gen

resolves the product map and runs `merge_config.sh -m -y <frags>` then
`olddefconfig`, writing `linux/.config`. `debian/rules` and CI call the same
target. `make check-fragments` validates every product (conflicting symbols,
values that fail to land).

## Updating for a new upstream kernel

After bumping `TAG` in `upstream.env` and running `./prepare.sh build`:

1. `make check-fragments` — names fragment values that no longer land (symbol
   removed, renamed, or dependency changed). Locate the line with
   `python3 configs/configtool.py where CONFIG_X`, then fix or drop it.
2. `make unipi-<p>_defconfig` for each product and review the merge warnings.
3. Optional: `merge_config.sh -r` lists lines that became redundant (now equal
   to the kernel default); pruning keeps the fragments minimal. Harmless if left.
4. If an upstream default changes behaviour you rely on, pin it in the relevant
   fragment with a `#` comment explaining why.

## Editing

`make unipi-<p>_defconfig && make menuconfig`, then `make report-<p>` lists
symbols not represented by any fragment plus value changes; move them into the
right fragment and re-run until `report` prints `clean`.
