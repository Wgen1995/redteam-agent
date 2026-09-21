#!/bin/bash
# 黄金夹具回归（批次 1）：规范化输出 vs golden/ 期望，exit 0/1
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
FIX="$HERE/fixtures/G-g1"; GOLD="$HERE/golden"; OUT="$(mktemp -d)"
run() { python3 "$HERE/../cli/tanyin-ledger" "$1" --goal-dir "$FIX" $2 | python3 "$HERE/normalize.py"; }
fail=0
for spec in "validate" "verify-chain" "next-id intents INT g1"; do
  set -- $spec
  name=$1
  if [ "$name" = "next-id" ]; then run "$1" "$2 $3 $4" > "$OUT/$name.norm"; else run "$1" "" > "$OUT/$name.norm"; fi
  if [ ! -f "$GOLD/$name.norm" ]; then cp "$OUT/$name.norm" "$GOLD/$name.norm"; echo "INIT $name"; continue; fi
  if ! diff -q "$GOLD/$name.norm" "$OUT/$name.norm" >/dev/null; then echo "FAIL $name"; diff "$GOLD/$name.norm" "$OUT/$name.norm" | head -5; fail=1; else echo "PASS $name"; fi
done
rm -rf "$OUT"; exit $fail