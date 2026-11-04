# Creative Muse

Creative Muse is a free ChatGPT plugin offering original morning-pages journal prompts and artist’s-date ideas, inspired by *The Artist’s Way* by Julia Cameron. It complements the book rather than reproducing or replacing it.

It runs as a skill inside ChatGPT, with no external tools or backend.

Created by [Matthew Lilley](https://mattlilley.com).

## Repository contents

- [`plugin.json`](plugin.json) — Plugin manifest and listing metadata.
- [`skills/`](skills/) — Behavioural instructions and supporting files.
- [`assets/`](assets/) — Plugin icon.
- [`docs/`](docs/) — Website pages for the OpenAI listing: landing page, support, privacy policy and terms of service.
- [`scripts/package_plugin.py`](scripts/package_plugin.py) — Builds the plugin ZIP separately from the website files.

## Rebuilding the distribution

From the repository root, run:

```sh
python3 scripts/package_plugin.py
```

Requires Python 3 with no additional dependencies. The script reads the version from [`plugin.json`](plugin.json), validates the package files, and writes:

- `dist/creative-muse-<version>.zip` — The plugin upload package.
- `dist/creative-muse-<version>.contents.txt` — Validation results, file sizes and SHA-256 checksums.

Rebuild after changing any packaged file. Rebuilding the same version overwrites its ZIP and contents report; update `version` in `plugin.json` when preparing a new release. If you add a file that should be included in the plugin, add its path to `FILES` in `scripts/package_plugin.py`.

The ZIP contains only the files listed in `FILES`; the website in `docs/` is maintained separately. Local validation does not check live listing URLs or submit the plugin for review or publication.

Released under the [MIT licence](LICENSE).
