# FinPref-Align Agent Notes

## A800 Access

- Remote training target: A800 server under `/autodl-fs/data/finpref/project`.
- Prefer SSH key login. The SSH public key comment/identifier is `liuyibo20250502CUHKSZ`.
- Do not scrape passwords or private credentials from local logs. If key login fails, ask the user to repair key access or explicitly provide fresh authorization.
- Keep Hugging Face cache, model outputs, logs, and training artifacts under `/autodl-fs/data` to avoid filling the system disk.

