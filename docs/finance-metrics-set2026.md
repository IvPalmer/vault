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

## Follow-up 2026-09-14: the six leftovers, the Pronampe replan, and two bugs they exposed

**Why a record store seen twice was never learned.** `create_category` in the
CategoryManager wrote `category_type='variable'` — not a value in
`CATEGORY_TYPE_CHOICES`. Five of Palmer's categories carried it (Musica,
Familia, Triagem, Drogas, Consórcios e Financiamentos). Everything that filters
on `'Variavel'` skipped them silently: the VARIÁVEIS tab, budget adherence, and
`smart_categorize`'s learning corpus *and* the gate deciding which categories
learning may assign — so "SP DR BANANA" (Musica/Discos, twice) could not be
learned. `gastos_variaveis` was not affected (it excludes by category name).
Data repaired, creation path fixed (`50cd346`). Visible side effect: the
Analytics expense-composition chart now counts those categories as variável,
which is what they are.

**The six rows.** Dr Banana and Zurco (a vinyl store in Santa Cruz, Bolivia,
same January trip as the Hipermaxi rows) → Musica/Discos; Amarket (Santa Cruz
supermarket) → Alimentação/Mercado; La Boheme (bar in Samaipata) →
Alimentação/Restaurante e Bares. "Crewza 24 01" and "Textura24 01" were left
alone: they are legacy checking rows (no `external_id`) two days off the
Pluggy PIX rows for the same R$100 and R$405 — phantom duplicates the ±1-day
dedup does not pair. They inflate January's totals by R$505; deleting them is
the operator's call.

**Pronampe amortization moved to Jan/27.** Template `contract_start`
2026-09 → 2027-01 (end Fev/27 and the R$5.8k Fev override kept); the reserve
gets a R$8k override Set–Dez/26 (3k + the 5k that would have amortized).
This exposed the carryover fallback in `get_metricas`: a mapping row that
outlives its template window returned expected 0 and fell back to
`default_limit`, reviving R$5k of "pending" debt in Nov, Dec and Jan. Guarded
with the same active-in-month rule the Controle uses (`876f454`); the three
orphaned rows were also deleted. Same commit: `get_cashflow_diario` scheduled
fixos/investments at `default_limit`, ignoring month overrides — the reserve
now lands at R$8k on day 5 in the vale chart.

**Installments from 1/N.** All 72 series with invoice ≥ Mar/26 are internally
consistent; category is set on 1/N at sync via Pluggy and propagated by
`reconcile_installment_series_categories`. That is consistency today, not a
guarantee at import: a 1/N Pluggy cannot classify starts NULL and is filled
by the nightly categorize + reconciliation (majority of siblings; a manual
position is protected). The remaining gap is subcategory when Pluggy's code is
parent-only with no subcategory in the mapping (Palmer: COMFYCOMBR 1/6,
DECATHLON 1/2; Rafa: `08000000 → Compras` has no subcategory, which is most of
her rows).

## Follow-up 2026-09-14 (2): the Subcategoria column

What the operator was actually looking at: rows with a category and "—" for
subcategory — NETFLIX.COM, OPENAI, BRADESCO AUT, PSICOLOGO, COUNTS, the
consórcio parcels — every month, plus installments. Two causes:

1. `smart_categorize` only selected rows with **no category**. Sync
   categorizes at Pluggy's level; when the mapping is parent-only the row gets
   a category and no subcategory and is never revisited, even with five earlier
   NETFLIX.COM rows carrying Streaming Video.
2. `DESCRIPTION_SUBCATEGORY_MAP` is keyed by category name using Rafa's
   taxonomy ("Servicos Digitais", "Compras"). Palmer's are "Assinaturas" and
   "Compras Gerais", so the keyword refinement never fired for him.

New `_fill_missing_subcategories` pass inside `smart_categorize` (both the
early-return and the normal path), before installment reconciliation, confined
to the row's own category — it never moves a category: Pluggy mapping with a
subcategory → first matching rule → keyword map → history keyed by
(category, digit-stripped description) with ≥2 rows and a >50% weighted
majority. Nightly at the 0.90 floor. First run: Palmer 88 rows, Rafa 245 (164 of
hers from Pluggy mappings that already carried a subcategory the rows never
received). Still "—" afterwards: rows with no history in that category and no
rule (Hoppin, LC POSTOS, COMFYCOMBR; most of Rafa's "Compra no débito|…" under
Compras, whose Pluggy code 08000000 maps to Compras with no subcategory).

Three things codex made explicit: installment siblings are reconciled *before*
the pass (evidence from the same purchase beats the merchant's history) and
again after; rows a human touched (`is_manually_categorized`) are never
filled — and the transaction PATCH now sets that flag whenever it touches
category/subcategory, so "Remover subcategoria" survives the night; and
`smart_categorize`'s dry run is now the real run inside a rolled-back
savepoint, so the preview is exactly what `--apply` does (the old skip-the-save
preview could show Geral where the apply gave Roupas).
