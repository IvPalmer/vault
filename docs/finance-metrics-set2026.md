# Finance Metrics — September 2026: auto-classify and auto-link go unattended

Reported 2026-09-13: "auto assign and auto classify aren't working right; many
purchases and installments aren't auto-mapped or categorized."

## What was actually wrong

Three things, none of them what the symptom suggested.

1. **Neither engine ran on its own.** `smart_categorize` only ran from the
   "Categorizar" button on Visão Mensal; `auto_link_recurring` only from
   "⚡ Auto-link" on Controle. Sync applies Pluggy's category plus keyword
   rules at insert time and nothing else, so a charge Pluggy does not classify
   (Anthropic, Beatport, Bandcamp, Yoyaku — foreign merchants) stayed
   uncategorized until someone clicked, and a fixo paid on the 11th stayed
   "Faltando" until someone clicked.
2. **The link matcher was wrong more often than right.** Simulated on
   September data inside a rolled-back transaction it made 6 links, 4 wrong:
   LUZ took the accountant's PIX (both begin "Pagamento de Pix QR Code",
   within 5%), CONTADOR then took a gas station (amount-only ±10%), VIVO took
   the Bradesco car insurance (amount-only), FAMILIA took a charity donation
   whose description contains "FAMILIAS" (substring). Had it been wired into
   the nightly run as it was, it would have corrupted the controle silently.
3. **The categorizer's amount-pattern strategy is noise.** At the button's
   0.70 floor, "three earlier charges of ~R$28 on this card were food" filed
   Beatport under Alimentação, a cannabis shop under Limpeza e Manutenção,
   Traders Club under Pet Shop and a R$149 record store under Farmácia.

## What changed

**`auto_link_recurring` rewritten** (`api/services.py`, 15 tests in
`api/tests/test_auto_link_recurring.py`). An item is recognised by the
*description* it was linked to in a previous month (up to 3 back, custom /
renamed months excluded), digits stripped (`_link_key`) because Bradesco
stamps the month into the text. One slot per previous link, so the second
salary parcel still fits after the first is linked. Assignment is global and
greedy by amount distance to a reference — last month's amount (or this
month's expected, for single-payment items whose amount the user changed);
the Pluggy bill total for cards, which is the only thing that tells the two
"Pagamento de boleto ITAU UNIBANCO" apart — bounded by a 50% guard. A card
with no bill total yet is not linked by either pass. Name similarity survives
only for items with no history at all, whole-word. **There is no amount-only
strategy.** Transactions owned by any mapping (including cross-month links)
are off the table. `dry_run` added.

**Two pipeline stages** after `dedup`, before `phantom`/`audit`:
`smart_categorize` (global, `--min-confidence 0.90`: Pluggy, keyword rules,
Apple-by-amount and exact-description history; amount-pattern and token
similarity stay behind the button) and `auto_link_recurring` (current and
previous month). Both dry-run unless `--apply`, so the pipeline's staleness
and maintenance gates apply to them.

## Verified before deploy

- 174/174 backend tests in the container's throwaway test database.
- Dry run on production data: auto-link Sep → 4/12 linked, all correct
  (CONTADOR, TERAPIA, PROASA, SEGURO BRADESCO); the other 8 are genuinely not
  paid yet on the 13th. `smart_categorize` at 0.90 → 3 rows (Anthropic via
  exact history, two boletos via Pluggy's parent fallback); 508 legacy rows
  (2022–2025 imports) remain for a human.
- Three rounds of adversarial review with codex; 15 findings, 12 applied.

## Known limits (deliberate)

- A card bill paid in two parts links only one part when last month had one
  payment; the item shows Parcial. Not seen in this data.
- An explicit "uncategorize" in the UI keeps `pluggy_category_id`, so the
  nightly run re-applies Pluggy's category (the button always did the same).
  Needs an opt-out the uncategorize views set — separate change.
- Rows Pluggy cannot classify and that have no history need a keyword rule;
  BANDCAMP / BEATPORT / YOYAKU / BLOOP / DEEJAY / TRAXSOURCE → Musica were
  added as rules from 140+ rows of unambiguous history the same day.
