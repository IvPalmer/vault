# Pluggy Open Finance Integration

## Summary

Pluggy.ai is a BCB-authorized Open Finance aggregator that provides REST API access to Brazilian bank data. Verified 2026-03-05 against Itaú PF accounts via the Open Finance OAuth flow.

## Setup

### Dashboard & Credentials

- Developer portal: https://dashboard.pluggy.ai
- Consumer app: https://meu.pluggy.ai
- API docs: https://docs.pluggy.ai

### Itaú Connector

- **Connector ID**: 601 (Itaú PF, Open Finance, OAuth)
- **Credential required**: CPF only
- **Products**: ACCOUNTS, TRANSACTIONS, IDENTITY, CREDIT_CARDS, PAYMENT_DATA, LOANS, INVESTMENTS

### Connected Accounts

| Account | Type | Pluggy ID |
|---------|------|-----------|
| Checking | BANK/CHECKING_ACCOUNT | `<account-uuid-1>` |
| Savings | BANK/SAVINGS_ACCOUNT | `<account-uuid-2>` |
| Credit Card 1 | CREDIT/CREDIT_CARD | `<account-uuid-3>` |
| Credit Card 2 | CREDIT/CREDIT_CARD | `<account-uuid-4>` |
| CDB Itaú | FIXED_INCOME | (via /investments endpoint) |

## API Reference

### Authentication

```bash
# Get API key (expires 2h)
POST https://api.pluggy.ai/auth
{"clientId": "...", "clientSecret": "..."}
# Returns: {"apiKey": "..."}
```

### Key Endpoints

```
GET /accounts?itemId={itemId}
GET /transactions?accountId={accountId}&from=YYYY-MM-DD&to=YYYY-MM-DD&pageSize=N
GET /investments?itemId={itemId}
GET /identity?itemId={itemId}
```

All requests use header: `X-API-KEY: {apiKey}`

### Transaction Schema

```json
{
  "id": "uuid",
  "description": "PIX TRANSF FULANO01/01",
  "descriptionRaw": "PIX TRANSF FULANO01/01",
  "currencyCode": "BRL",
  "amount": -100.00,
  "date": "2026-01-01T12:00:00.000Z",
  "category": "Transfer - PIX",
  "categoryId": "05070000",
  "status": "POSTED",
  "type": "DEBIT",
  "operationType": "PIX",
  "paymentData": {
    "payer": { "documentNumber": {"type": "CPF", "value": "..."} },
    "paymentMethod": "PIX",
    "receiver": { "documentNumber": {"type": "CPF", "value": "..."} }
  }
}
```

Key fields: `amount` (negative = debit), `category` (auto-assigned), `paymentData` (PIX counterparty info).

### Data Volumes

Expect tens-to-hundreds of transactions per account per month; page with `pageSize`.

## OAuth Flow

1. `POST /items` with `connectorId: 601` + CPF → creates Item
2. `GET /items/{id}` → status `WAITING_USER_INPUT` with OAuth URL in `parameter.data`
3. User opens URL in browser → Itaú login → consent → redirect to `data.of.pluggy.ai/cb`
4. Item auto-syncs through: ACCOUNTS → CREDITCARDS → TRANSACTIONS → LOANS → INVESTMENTS → SUCCESS (~30-45s)

### OAuth Caveats

- **One-time URL**: The auth link is consumed on first visit. Messaging app previews (Slack, WhatsApp) will invalidate it.
- **Geo-restriction**: Itaú's OAuth endpoint (`id.opf.itau.com.br`) blocks non-Brazilian IPs. Must use Brazilian IP.
- **Expiration**: URL expires ~20 minutes after creation.
- **Direct open**: Use `open "URL"` on macOS to avoid copy-paste mangling.

## Trial & Pricing

### Trial (16 days from signup)

- Full API access, up to 100 Items
- All features including Open Finance connectors
- No credit card required

### After Trial (confirmed 2026-03-26)

- **Direct item refresh blocked** — `PATCH /items/{id}` returns 403 (sandbox-only)
- **Read endpoints still work** — transactions, accounts, bills all accessible
- **Cannot add new connections** or edit connector configuration
- Sandbox items deleted after 30 days of inactivity

### MeuPluggy Proxy (Free, Post-Trial Solution)

MeuPluggy (meu.pluggy.ai) is a free consumer app that maintains bank connections via Open Finance.
By linking the dev account to MeuPluggy, API reads go through a proxy that refreshes daily.

**Setup steps (one-time):**
1. Sign in to meu.pluggy.ai — bank connections from trial persist here
2. Dashboard → Customization → Connectors → enable MeuPluggy (Direct Connector)
3. Dashboard → Applications → Vault app → ▷ Demo → Connect Account → MeuPluggy
4. Authorize each bank (Itaú, Nubank) via MeuPluggy OAuth
5. New proxy items appear with fresh data; update PROFILE_CONFIG in sync_pluggy.py

**Post-setup behavior:**
- MeuPluggy refreshes data daily (~03:30 UTC)
- `sync_pluggy` reads transactions/bills/balances normally (no `--refresh` needed)
- `update_item()` handles 403 gracefully — logs warning, returns current item state
- Old direct items remain accessible but frozen at last refresh date

### MeuPluggy Items (active)

#### Profile A (Itaú) — Item: `<account-uuid-5>`

| Account | Type | Pluggy ID |
|---------|------|-----------|
| Checking | BANK | `<account-uuid-6>` |
| Savings | BANK | `<account-uuid-7>` |
| Credit Card 1 | CREDIT | `<account-uuid-8>` |
| Credit Card 2 | CREDIT | `<account-uuid-9>` |

#### Profile B (Nubank) — Item: `<account-uuid-10>`

| Account | Type | Pluggy ID |
|---------|------|-----------|
| NuBank Conta | BANK | `<account-uuid-11>` |
| NuBank Cartão | CREDIT | `<account-uuid-12>` |

## Balance anchors & month-end realignment

`BalanceAnchor` rows store the checking balance on a date. Closed-month opening
balances come from `_get_checking_balance_eom()` (services.py), which reads the
anchor **on** the month-end date (or rolls the latest in-month anchor forward).

**Gotcha — Pluggy anchor date = sync date, not balance date.** The daily sync
(`sync_pluggy --save-balance`) stamps each anchor with the *sync* date, but
MeuPluggy lags the bank by ~1-2 days, so an anchor "dated" the 29th may actually
hold the 27th's balance. At a month boundary this skews the next month's opening
by whatever posted in the missed days.

Example: a month opens at the anchor's figure, but the Itaú statement shows a
lower end-of-previous-month balance — a late-month PIX the lagged anchor missed.
The bank statement's end-of-month "SALDO DO DIA" is authoritative.

**Realignment (do this whenever a month-end looks off):** take the exact EOM
balance from the statement and drop an anchor on the last day of the month:

```
manage.py set_balance_anchor --profile <name> --date 2026-05-31 --balance 1234.56
```

`_get_checking_balance_eom` then returns it exactly (step 1: anchor on month-end).
The daily sync only writes current-date anchors, so a manual month-end anchor is
never overwritten. Note: loan proceeds that land in checking (categorized
`Emprestimos`, `is_internal_transfer=True`) ARE part of the real balance and
correctly included in the opening — only income that posts *after* month-end
(e.g. salary on the 1st) is excluded.

### Paid Plans

| Plan | Cost | Notes |
|------|------|-------|
| Basic | R$ 2,500/month | Open Finance + direct connections, help desk |
| Custom | Contact sales | High volume, premium support, BETA products |

Sources:
- Actual Budget docs: https://actualbudget.org/docs/advanced/bank-sync/pluggyai/
- MeuPluggy GitHub: https://github.com/pluggyai/meu-pluggy
- Pluggy pricing: https://www.pluggy.ai/en/pricing
