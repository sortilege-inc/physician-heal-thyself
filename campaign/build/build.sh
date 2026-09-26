#!/usr/bin/env bash
# The chronicle's own build: the cast layer (Maggie Molyneux and Fatima), the portraits, the public pages and the GM's pack, all from the Notion
# export in campaign/source/notion (campaign/source/import_notion.py takes a fresh export there).
# Run from anywhere; the books' data/ is upstream's and must already be built (the pages' book
# filter reads it).
#
#   bash campaign/build/build.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 campaign/source/convert_cast.py
bash build/build_layer.sh campaign/dsl campaign "Physician, Heal Thyself" campaign/data
python3 campaign/source/check_cast.py
python3 campaign/build/build_portraits.py
python3 campaign/build/build_docs.py
python3 campaign/build/build_seed.py
node --check campaign/data/docs.js
node --check campaign/site/site.js
node -e "JSON.parse(require('fs').readFileSync('campaign/pack/seed.json','utf8'))"
echo "campaign build: OK"
