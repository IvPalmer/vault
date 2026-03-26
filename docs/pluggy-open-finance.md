# Pluggy Open Finance Integration

## Summary

Pluggy.ai is a BCB-authorized Open Finance aggregator that provides REST API access to Brazilian bank data. Successfully tested on 2026-03-05 with Palmer's Itaú accounts via Open Finance OAuth flow.

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
| Checking | BANK/CHECKING_ACCOUNT | `535be1c8-5191-4f1f-8591-8d607538a883` |
| Savings | BANK/SAVINGS_ACCOUNT | `ef7635dc-1b6e-4843-b663-eee4e672e21a` |
| Master CC | CREDIT/CREDIT_CARD | `feb08f5e-d151-40d4-b816-89647b9b7b19` |
| Visa CC | CREDIT/CREDIT_CARD | `22935e0c-0484-46fb-b638-5be4c03d3331` |
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
  "description": "PIX TRANSF ROSILDA04/03",
  "descriptionRaw": "PIX TRANSF ROSILDA04/03",
  "currencyCode": "BRL",
  "amount": -220.00,
  "date": "2026-03-04T20:06:17.090Z",
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

### Data Volumes Observed

- Checking: 56 transactions (Feb-Mar 2026)
- Master CC: 129 transactions
- Visa CC: 37 transactions

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

#### Palmer (Itaú) — Item: `efd32560-e14d-41ac-9ea8-f788f073ca57`

| Account | Type | Pluggy ID |
|---------|------|-----------|
| Checking | BANK | `ccffdde0-6624-4fa2-8e16-4826b38072b4` |
| Savings | BANK | `e595441e-cb10-4a00-90d1-89a1e23daac9` |
| Mastercard Black | CREDIT | `8a92ed78-9961-4a7c-88ed-e13c21d3ceea` |
| Visa Infinite | CREDIT | `7e611459-0243-4f30-8c21-e788200114c4` |

#### Rafa (Nubank) — Item: `a97e5072-fb66-4352-97e9-1d54620d4eeb`

| Account | Type | Pluggy ID |
|---------|------|-----------|
| NuBank Conta | BANK | `ef7d504f-c4ef-44b9-afe0-8086e5a4f846` |
| NuBank Cartão | CREDIT | `eaa5556b-f38b-4b1e-9e68-fffdca6f1a9a` |

### Paid Plans

| Plan | Cost | Notes |
|------|------|-------|
| Basic | R$ 2,500/month | Open Finance + direct connections, help desk |
| Custom | Contact sales | High volume, premium support, BETA products |

Sources:
- Actual Budget docs: https://actualbudget.org/docs/advanced/bank-sync/pluggyai/
- MeuPluggy GitHub: https://github.com/pluggyai/meu-pluggy
- Pluggy pricing: https://www.pluggy.ai/en/pricing
