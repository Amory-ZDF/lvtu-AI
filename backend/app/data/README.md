# Private seed data directory

This directory is intentionally kept without real data in the public repository.

For local development, store seed JSON files in a private folder, for example:

```bash
/Users/zhangdifei03/Desktop/旅途重构/lv_private_data/seed_data/
```

Then import them with:

```bash
cd backend
LV_SEED_DATA_DIR="/path/to/lv_private_data/seed_data" python -m scripts.seed_knowledge --reset
```

Do not commit real seed data, database dumps, user uploads, API keys, or `.env` files.
