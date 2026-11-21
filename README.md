# SKYHOLD

A travel poster for a place that isn't there.

SKYHOLD is a ring-cliff city floating above the clouds, its waterfalls
falling into the sky at golden dusk. This repository is my entry for the
make.fun bounty [The Poster for a Place That Isn't There](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539).

## What's here

- `asset.jpg` — the finished SKYHOLD poster (1024×1024 JPEG).
- `main.py` — the entry program. It finds `asset.jpg` next to itself,
  checks that it is a real JPEG within the limits (magic bytes
  `FF D8 FF`, at most 1,048,576 bytes, at most 1024×1024 pixels — the
  dimensions are read straight from the JPEG start-of-frame segment),
  then writes it out as `entry.png` in the output directory
  (`$MAKEFUN_OUTPUT_DIR`, else `/output` when it exists, else
  `./output`). Stale files inside the output directory are cleared,
  the directory itself is never removed, and the entry is written
  through a temporary file plus rename. Anything that fails validation
  exits non-zero with a plain error message.

## Run it

```sh
python3 main.py
```

## License

MIT — see `LICENSE`.
