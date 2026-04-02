# Pluggy Dedup Cleanup & Sync Hardening

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete ~1,309 duplicate transactions caused by MeuPluggy migration/bill-vs-account double import, fix 5 date-swapped and 3 orphaned records, and harden sync_pluggy to prevent recurrence.

**Architecture:** All cleanup runs as Django shell scripts inside Docker (`docker compose exec backend python manage.py shell -c "..."`). Dedup hardening modifies `sync_pluggy.py` only. Each cleanup step captures before/after counts and validates totals. A final management command `validate_pluggy_consistency` is added for ongoing regression checking.

**Tech Stack:** Django ORM, Pluggy REST API, Docker Compose

---

### Task 1: Snapshot baseline counts for validation

**Files:**
- None (read-only)

- [ ] **Step 1: Capture per-account transaction counts and totals**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile
from django.db.models import Sum, Count

for pname in ['Palmer', 'Rafa']:
    p = Profile.objects.get(name=pname)
    print(f'\\n=== {pname} ===')
    for acct in p.accounts.all().order_by('name'):
        qs = Transaction.objects.filter(profile=p, account=acct)
        total = qs.count()
        pluggy = qs.exclude(external_id='').count()
        legacy = qs.filter(external_id='').count()
        amt = qs.aggregate(s=Sum('amount'))['s'] or 0
        print(f'  {acct.name}: total={total} pluggy={pluggy} legacy={legacy} sum={amt}')
    total_all = Transaction.objects.filter(profile=p).count()
    print(f'  TOTAL: {total_all}')
"
```

Save the output — this is the baseline. After all cleanup steps, re-run and compare.

- [ ] **Step 2: Record expected deletions**

Expected cleanup summary:
- Task 2: ~1,113 old-account Pluggy dupes (keep newer MeuPluggy external_ids)
- Task 3: ~95 bill-vs-account dupes (keep account-level with better descriptions)
- Task 4: ~48 exact dupes + ~14 boleto dupes + ~39 cross-account dupes = ~101
- Task 5: 5 date fixes + 3 orphan deletions = 8 records touched
- Total expected deletions: ~1,309-1,320 records

---

### Task 2: Delete old-account Pluggy duplicates (1,113 records)

**Files:**
- None (DB operations only)

These are transactions imported from pre-MeuPluggy account IDs. They have UPPERCASE descriptions while the MeuPluggy versions have Title Case. Same (account, date, amount) but different external_ids and different description casing.

- [ ] **Step 1: Identify and count old-account duplicates**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile
from collections import defaultdict
import unicodedata, re

def _norm(s):
    nfkd = unicodedata.normalize('NFKD', s)
    ascii_only = nfkd.encode('ASCII', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', ascii_only.lower())

total_dupes = 0
for pname in ['Palmer', 'Rafa']:
    p = Profile.objects.get(name=pname)
    pluggy_txns = Transaction.objects.filter(
        profile=p
    ).exclude(external_id='').select_related('account')

    # Group by (account_id, date, amount, normalized_desc)
    groups = defaultdict(list)
    for t in pluggy_txns:
        key = (t.account_id, str(t.date), str(t.amount), _norm(t.description))
        groups[key].append(t)

    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    extra = sum(len(v) - 1 for v in dupes.values())
    total_dupes += extra
    print(f'{pname}: {len(dupes)} groups, {extra} extra records')
    # Show 3 samples
    for i, (k, txns) in enumerate(list(dupes.items())[:3]):
        for t in txns:
            print(f'  {t.date} | {t.amount:>10} | {t.description[:45]} | ext={t.external_id[:12]}')
        print()

print(f'TOTAL old-account dupes: {total_dupes}')
"
```

Expected: ~1,113 extra records. Verify the pattern: pairs where one has UPPERCASE desc, other has Title Case.

- [ ] **Step 2: Delete old-account duplicates, keeping newer external_id**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile
from collections import defaultdict
import unicodedata, re

def _norm(s):
    nfkd = unicodedata.normalize('NFKD', s)
    ascii_only = nfkd.encode('ASCII', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', ascii_only.lower())

total_deleted = 0
for pname in ['Palmer', 'Rafa']:
    p = Profile.objects.get(name=pname)
    pluggy_txns = Transaction.objects.filter(
        profile=p
    ).exclude(external_id='').select_related('account')

    groups = defaultdict(list)
    for t in pluggy_txns:
        key = (t.account_id, str(t.date), str(t.amount), _norm(t.description))
        groups[key].append(t)

    to_delete_ids = []
    for key, txns in groups.items():
        if len(txns) <= 1:
            continue
        # Keep the one with the most recent created_at (MeuPluggy version)
        txns.sort(key=lambda t: t.created_at, reverse=True)
        to_delete_ids.extend(t.id for t in txns[1:])

    if to_delete_ids:
        deleted, _ = Transaction.objects.filter(id__in=to_delete_ids).delete()
        total_deleted += deleted
        print(f'{pname}: deleted {deleted}')
    else:
        print(f'{pname}: 0 to delete')

print(f'TOTAL deleted: {total_deleted}')
"
```

- [ ] **Step 3: Validate — re-run count from Step 1, confirm delta matches**

Re-run the baseline count script from Task 1, Step 1. The total should be down by the number deleted in Step 2.

---

### Task 3: Delete bill-vs-account duplicates (95 records)

**Files:**
- None (DB operations only)

Same CC transaction imported from both bill endpoint (human-readable desc like "Figma") and account endpoint (raw merchant string like "FIGMA FIGMA.COM US"). Different external_ids, different descriptions, but same date+amount+account.

- [ ] **Step 1: Identify bill-vs-account duplicates**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile
from collections import defaultdict
import unicodedata, re

def _norm(s):
    nfkd = unicodedata.normalize('NFKD', s)
    ascii_only = nfkd.encode('ASCII', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', ascii_only.lower())

total_extra = 0
for pname in ['Palmer', 'Rafa']:
    p = Profile.objects.get(name=pname)
    # Only CC accounts
    cc_txns = Transaction.objects.filter(
        profile=p, account__account_type='credit_card'
    ).exclude(external_id='').select_related('account')

    # Group by (account_id, date, amount) — different descriptions = bill vs account
    groups = defaultdict(list)
    for t in cc_txns:
        key = (t.account_id, str(t.date), str(t.amount))
        groups[key].append(t)

    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    # Filter: only count groups where descriptions differ (normalized)
    bill_acct_dupes = {}
    for k, txns in dupes.items():
        norms = set(_norm(t.description) for t in txns)
        if len(norms) > 1:
            bill_acct_dupes[k] = txns

    extra = sum(len(v) - 1 for v in bill_acct_dupes.values())
    total_extra += extra
    print(f'{pname}: {len(bill_acct_dupes)} groups, {extra} extra records')
    for i, (k, txns) in enumerate(list(bill_acct_dupes.items())[:5]):
        for t in txns:
            print(f'  {t.date} | {t.amount:>10} | {t.description[:50]} | ext={t.external_id[:12]}')
        print()

print(f'TOTAL bill-vs-account dupes: {total_extra}')
"
```

- [ ] **Step 2: Delete bill-vs-account duplicates, keeping shorter description (account-level)**

Strategy: keep the record with the shorter description (typically the human-readable bill version like "Figma" vs "FIGMA FIGMA.COM US"). If same length, keep most recently created.

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile
from collections import defaultdict
import unicodedata, re

def _norm(s):
    nfkd = unicodedata.normalize('NFKD', s)
    ascii_only = nfkd.encode('ASCII', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', ascii_only.lower())

total_deleted = 0
for pname in ['Palmer', 'Rafa']:
    p = Profile.objects.get(name=pname)
    cc_txns = Transaction.objects.filter(
        profile=p, account__account_type='credit_card'
    ).exclude(external_id='').select_related('account')

    groups = defaultdict(list)
    for t in cc_txns:
        key = (t.account_id, str(t.date), str(t.amount))
        groups[key].append(t)

    to_delete_ids = []
    for k, txns in groups.items():
        if len(txns) <= 1:
            continue
        norms = set(_norm(t.description) for t in txns)
        if len(norms) <= 1:
            continue  # Same description = handled in Task 2
        # Keep shortest description (human-readable), then newest
        txns.sort(key=lambda t: (len(t.description), -t.created_at.timestamp()))
        to_delete_ids.extend(t.id for t in txns[1:])

    if to_delete_ids:
        deleted, _ = Transaction.objects.filter(id__in=to_delete_ids).delete()
        total_deleted += deleted
        print(f'{pname}: deleted {deleted}')
    else:
        print(f'{pname}: 0 to delete')

print(f'TOTAL deleted: {total_deleted}')
"
```

- [ ] **Step 3: Validate counts**

Re-run baseline count script. Confirm delta matches.

---

### Task 4: Delete remaining duplicates (exact + boleto + cross-account)

**Files:**
- None (DB operations only)

Three sub-categories:
- **Exact dupes**: Same (account, date, amount, description) — leftover after Task 2
- **Boleto dupes**: Checking transactions with same date+amount but different description casing (e.g., "PAG BOLETO ITAU UNIBANCO" vs "Pag Boleto Itau Unibanco")
- **Cross-account dupes**: Same external_id on both MC Black and MC Rafa (Rafa is additional card)

- [ ] **Step 1: Identify and delete all three sub-categories**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile
from collections import defaultdict
import unicodedata, re

def _norm(s):
    nfkd = unicodedata.normalize('NFKD', s)
    ascii_only = nfkd.encode('ASCII', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', ascii_only.lower())

total_deleted = 0

# --- A) Exact duplicates (same account, date, amount, description) ---
for pname in ['Palmer', 'Rafa']:
    p = Profile.objects.get(name=pname)
    all_txns = Transaction.objects.filter(profile=p).exclude(external_id='').select_related('account')

    groups = defaultdict(list)
    for t in all_txns:
        key = (t.account_id, str(t.date), str(t.amount), t.description.strip())
        groups[key].append(t)

    to_delete = []
    for k, txns in groups.items():
        if len(txns) > 1:
            txns.sort(key=lambda t: t.created_at, reverse=True)
            to_delete.extend(txns[1:])

    if to_delete:
        ids = [t.id for t in to_delete]
        deleted, _ = Transaction.objects.filter(id__in=ids).delete()
        total_deleted += deleted
        print(f'{pname} exact dupes: deleted {deleted}')
    else:
        print(f'{pname} exact dupes: 0')

# --- B) Boleto dupes (same date+amount, different casing, checking accounts) ---
for pname in ['Palmer', 'Rafa']:
    p = Profile.objects.get(name=pname)
    checking_txns = Transaction.objects.filter(
        profile=p, account__account_type='checking'
    ).exclude(external_id='').select_related('account')

    groups = defaultdict(list)
    for t in checking_txns:
        key = (t.account_id, str(t.date), str(t.amount), _norm(t.description))
        groups[key].append(t)

    to_delete = []
    for k, txns in groups.items():
        if len(txns) > 1:
            # Verify these are case-variant dupes (different descriptions, same normalized)
            descs = set(t.description for t in txns)
            if len(descs) > 1:
                txns.sort(key=lambda t: t.created_at, reverse=True)
                to_delete.extend(txns[1:])

    if to_delete:
        ids = [t.id for t in to_delete]
        deleted, _ = Transaction.objects.filter(id__in=ids).delete()
        total_deleted += deleted
        print(f'{pname} boleto dupes: deleted {deleted}')
    else:
        print(f'{pname} boleto dupes: 0')

# --- C) Cross-account dupes (same external_id on MC Black + MC Rafa) ---
from django.db.models import Count
dup_ext_ids = (
    Transaction.objects.exclude(external_id='')
    .values('external_id')
    .annotate(cnt=Count('id'))
    .filter(cnt__gt=1)
    .values_list('external_id', flat=True)
)
to_delete = []
for ext_id in dup_ext_ids:
    txns = list(Transaction.objects.filter(external_id=ext_id).select_related('account'))
    if len(txns) > 1:
        # Keep the one on the correct account (MC Rafa for card_last4=5780, else MC Black)
        for t in txns:
            if t.card_last4 == '5780' and 'Rafa' not in t.account.name:
                to_delete.append(t)  # Wrong account
            elif t.card_last4 != '5780' and 'Rafa' in t.account.name:
                to_delete.append(t)  # Wrong account

if to_delete:
    ids = [t.id for t in to_delete]
    deleted, _ = Transaction.objects.filter(id__in=ids).delete()
    total_deleted += deleted
    print(f'Cross-account dupes: deleted {deleted}')
else:
    # Fallback: just keep one per external_id
    for ext_id in dup_ext_ids:
        txns = list(Transaction.objects.filter(external_id=ext_id).order_by('-created_at'))
        if len(txns) > 1:
            to_delete.extend(txns[1:])
    if to_delete:
        ids = [t.id for t in to_delete]
        deleted, _ = Transaction.objects.filter(id__in=ids).delete()
        total_deleted += deleted
        print(f'Cross-account dupes (fallback): deleted {deleted}')
    else:
        print('Cross-account dupes: 0')

print(f'\\nTOTAL deleted in Task 4: {total_deleted}')
"
```

- [ ] **Step 2: Validate counts**

Re-run baseline count script. Confirm cumulative delta matches Tasks 2+3+4.

---

### Task 5: Fix date-swapped and orphaned records

**Files:**
- None (DB operations only)

- [ ] **Step 1: Fix 5 date-swapped records (MM/DD swap)**

These are Visa international subscriptions where the date was swapped (e.g., Pluggy says Apr 5 but DB has Nov 4 — month and day swapped).

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile
from api.pluggy import PluggyClient
import os, requests
from datetime import date

p = Profile.objects.get(name='Palmer')
c = PluggyClient(os.environ['PLUGGY_CLIENT_ID'], os.environ['PLUGGY_CLIENT_SECRET'])
headers = c._headers()

# Find Visa Pluggy transactions and check for date swaps
visa_txns = Transaction.objects.filter(
    profile=p, account__name='Visa Infinite'
).exclude(external_id='').order_by('date')

fixed = 0
for t in visa_txns:
    # Check if swapping month/day gives a valid date that might match Pluggy
    try:
        swapped = date(t.date.year, t.date.day, t.date.month)
    except ValueError:
        continue
    if swapped == t.date:
        continue
    # Only check if month > 12 is impossible (so swap would have been caught)
    # Check Pluggy for the real date
    resp = requests.get(f'https://api.pluggy.ai/transactions/{t.external_id}',
                        headers=headers, timeout=10)
    if not resp.ok:
        continue
    pluggy_date = date.fromisoformat(resp.json()['date'][:10])
    if pluggy_date != t.date and pluggy_date == swapped:
        print(f'FIX: {t.description[:40]} DB={t.date} Pluggy={pluggy_date}')
        t.date = pluggy_date
        t.month_str = pluggy_date.strftime('%Y-%m')
        t.save(update_fields=['date', 'month_str'])
        fixed += 1

print(f'Fixed {fixed} date-swapped records')
"
```

Note: This will be slow (checks all Visa Pluggy txns). If the agent set found only 5 specific records, target them directly instead. Expected: 5 fixes.

- [ ] **Step 2: Remove 3 orphaned records (404 from Pluggy)**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile

p = Profile.objects.get(name='Palmer')
orphan_ext_ids = [
    'a41a03a5',  # IOF COMPRA INTERNACIONA, Mar 18
    '4c0b6b62',  # DL *GOOGLE ADS2044, Mar 18
    '591814ec',  # Patreon* Membership, Mar 18
]
deleted = 0
for prefix in orphan_ext_ids:
    qs = Transaction.objects.filter(profile=p, external_id__startswith=prefix)
    count = qs.count()
    if count:
        qs.delete()
        deleted += count
        print(f'Deleted {count} record(s) with ext_id starting {prefix}')

print(f'Total orphans deleted: {deleted}')
"
```

- [ ] **Step 3: Validate counts**

Re-run baseline count. Confirm total delta = Tasks 2+3+4+5.

---

### Task 6: Harden sync_pluggy dedup logic

**Files:**
- Modify: `backend/api/management/commands/sync_pluggy.py`

Three changes to prevent recurrence:
1. **Case-insensitive content dedup**: Normalize descriptions when building the content dedup index
2. **Bill-vs-account awareness**: When a CC transaction has no billId but a billed_month match exists, also check by (date, amount) against existing Pluggy records regardless of description
3. **Cross-account dedup**: Include routed accounts in the content dedup index

- [ ] **Step 1: Update the content-based dedup to normalize descriptions**

In `_sync_transactions`, change the content dedup index and check to use normalized descriptions:

```python
# In sync_pluggy.py, replace the existing content-based dedup block

        # Content-based dedup for Pluggy transactions (catches re-imported txns
        # with new external_ids from MeuPluggy refreshes).
        # Normalize descriptions for case-insensitive matching (bill endpoint
        # returns Title Case, account endpoint returns UPPERCASE).
        def _content_norm(s):
            """Normalize for content dedup: lowercase, strip, collapse whitespace."""
            return re.sub(r'\s+', ' ', s.strip().lower())

        # Index by (amount, norm_desc) -> set of dates for ±1 day tolerance.
        existing_pluggy_by_content = {}  # (amount, norm_desc) -> set of dates
        # Also index by (date, amount) for description-agnostic dedup (bill vs account)
        existing_pluggy_by_date_amt = {}  # (date, amount) -> True
        for t in Transaction.objects.filter(
            account_id__in=acct_ids, profile=self.profile
        ).exclude(external_id='').values_list('date', 'amount', 'description'):
            ckey = (t[1], _content_norm(t[2]))
            existing_pluggy_by_content.setdefault(ckey, set()).add(t[0])
            existing_pluggy_by_date_amt[(t[0], t[1])] = True
```

- [ ] **Step 2: Update the content dedup check in the transaction loop**

Replace the existing content dedup check:

```python
            # Content-based dedup: skip if same (amount, normalized description) with
            # date ±1 day already exists from a previous Pluggy sync.
            # Handles MeuPluggy external_id changes AND bill-vs-account description diffs.
            content_key = (amount, _content_norm(description))
            existing_dates = existing_pluggy_by_content.get(content_key, set())
            if any(abs((txn_date - d).days) <= 1 for d in existing_dates):
                skipped_count += 1
                continue

            # Description-agnostic dedup for CC: same (date, amount) already imported.
            # Bill endpoint returns different descriptions than account endpoint.
            if is_cc and (txn_date, amount) in existing_pluggy_by_date_amt:
                skipped_count += 1
                continue

            # Track for future iterations in this batch
            existing_pluggy_by_content.setdefault(content_key, set()).add(txn_date)
            existing_pluggy_by_date_amt[(txn_date, amount)] = True
```

- [ ] **Step 3: Verify the edit compiles**

```bash
docker compose exec backend python -c "from api.management.commands.sync_pluggy import Command; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Run sync and verify 0 new duplicates created**

```bash
docker compose exec backend python manage.py sync_pluggy --profile Palmer 2>&1 | tail -15
docker compose exec backend python manage.py sync_pluggy --profile Rafa 2>&1 | tail -15
```

Expected: `Created 0 new` or small number of genuinely new recent transactions. No large batch of "new" records.

- [ ] **Step 5: Run sync a second time to confirm stability**

```bash
docker compose exec backend python manage.py sync_pluggy --profile Palmer 2>&1 | grep 'Done:'
docker compose exec backend python manage.py sync_pluggy --profile Rafa 2>&1 | grep 'Done:'
```

Expected: `0 new, 0 updated` on both runs.

- [ ] **Step 6: Commit**

```bash
git add backend/api/management/commands/sync_pluggy.py backend/api/pluggy.py
git commit -m "fix: harden sync_pluggy dedup — case-insensitive, bill-vs-account, content-based

Prevents duplicate imports from:
- MeuPluggy external_id regeneration
- Bill endpoint vs account endpoint (different descriptions)
- Case differences in boleto payment descriptions
- ±1 day date tolerance for posting date shifts

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Final validation

**Files:**
- None (read-only)

- [ ] **Step 1: Re-run baseline counts and compare**

Run the same script from Task 1, Step 1. Compare against the baseline. The difference should equal the total records deleted across Tasks 2-5.

- [ ] **Step 2: Check for any remaining duplicates**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile
from collections import defaultdict
import unicodedata, re

def _norm(s):
    nfkd = unicodedata.normalize('NFKD', s)
    ascii_only = nfkd.encode('ASCII', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', ascii_only.lower())

for pname in ['Palmer', 'Rafa']:
    p = Profile.objects.get(name=pname)
    pluggy = Transaction.objects.filter(profile=p).exclude(external_id='').select_related('account')

    # Exact dupes
    exact = defaultdict(list)
    for t in pluggy:
        key = (t.account_id, str(t.date), str(t.amount), t.description.strip())
        exact[key].append(t)
    exact_dupes = sum(len(v) - 1 for v in exact.values() if len(v) > 1)

    # Normalized dupes (case-insensitive)
    norm_groups = defaultdict(list)
    for t in pluggy:
        key = (t.account_id, str(t.date), str(t.amount), _norm(t.description))
        norm_groups[key].append(t)
    norm_dupes = sum(len(v) - 1 for v in norm_groups.values() if len(v) > 1)

    # Date+amount dupes on CC (bill vs account)
    cc = [t for t in pluggy if t.account.account_type == 'credit_card']
    da_groups = defaultdict(list)
    for t in cc:
        key = (t.account_id, str(t.date), str(t.amount))
        da_groups[key].append(t)
    da_dupes = sum(len(v) - 1 for v in da_groups.values() if len(v) > 1)

    print(f'{pname}: exact_dupes={exact_dupes} norm_dupes={norm_dupes} cc_date_amt_dupes={da_dupes}')

print('Target: all zeros (or very close)')
"
```

Expected: All zeros or near-zero.

- [ ] **Step 3: Run sync one more time to verify no regression**

```bash
docker compose exec backend python manage.py sync_pluggy --profile Palmer 2>&1 | grep 'Done:'
docker compose exec backend python manage.py sync_pluggy --profile Rafa 2>&1 | grep 'Done:'
```

Expected: `0 new` on both.

- [ ] **Step 4: Spot-check specific known issues from validation report**

```bash
docker compose exec backend python manage.py shell -c "
from api.models import Transaction, Profile

p = Profile.objects.get(name='Palmer')

# 1. Acuas should have no exact dupes
acuas = Transaction.objects.filter(profile=p, description__icontains='acuas').order_by('date')
print(f'Acuas records: {acuas.count()}')

# 2. No duplicate external_ids across the whole DB
from django.db.models import Count
dup_ext = (
    Transaction.objects.exclude(external_id='')
    .values('external_id')
    .annotate(cnt=Count('id'))
    .filter(cnt__gt=1)
    .count()
)
print(f'Duplicate external_ids: {dup_ext}')

# 3. Boleto payments on checking should have no case-variant dupes
import unicodedata, re
def _norm(s):
    nfkd = unicodedata.normalize('NFKD', s)
    ascii_only = nfkd.encode('ASCII', 'ignore').decode()
    return re.sub(r'[^a-z0-9]', '', ascii_only.lower())

from collections import defaultdict
boletos = Transaction.objects.filter(
    profile=p, account__account_type='checking',
    description__icontains='boleto'
).exclude(external_id='')
groups = defaultdict(list)
for t in boletos:
    key = (str(t.date), str(t.amount), _norm(t.description))
    groups[key].append(t)
boleto_dupes = sum(len(v) - 1 for v in groups.values() if len(v) > 1)
print(f'Boleto case-variant dupes: {boleto_dupes}')

print('\\nAll should be 0 (except Acuas count which should be reasonable)')
"
```
