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

### After Trial

- **Existing connections persist** — can still pull data from connected accounts
- **Cannot add new connections** or edit connector configuration
- Unclear if auto-sync/data refresh continues post-trial
- Sandbox items deleted after 30 days of inactivity

### Paid Plans

| Plan | Cost | Notes |
|------|------|-------|
| Basic | R$ 2,500/month | Open Finance + direct connections, help desk |
| Custom | Contact sales | High volume, premium support, BETA products |

**No free tier exists post-trial.**

### MeuPluggy (Free Consumer App)

- Connections persist indefinitely (Open Finance consent-based)
- Can export data as spreadsheet ("Baixar Relatório")
- Actual Budget project uses MeuPluggy for free long-term bank sync
- Key: set up ALL connections during trial period

Sources:
- Actual Budget docs: https://actualbudget.org/docs/advanced/bank-sync/pluggyai/
- Pluggy pricing: https://www.pluggy.ai/en/pricing
- Pluggy sandbox docs: https://docs.pluggy.ai/docs/sandbox

## Vault Integration Plan

### Approach

Django management command or scheduled task that:
1. Authenticates with Pluggy API (client_id/secret → API key)
2. Pulls transactions for all 4 accounts
3. Maps Pluggy schema to Vault's Transaction model
4. Deduplicates against existing imported data
5. Updates BalanceAnchor with current account balances

### Mapping (Pluggy → Vault)

| Pluggy field | Vault field |
|-------------|-------------|
| `description` | `description` |
| `amount` (abs) | `amount` |
| `amount` < 0 | `type` = expense |
| `date` | `date` |
| `category` | could map to Vault categories |
| `accountId` (checking) | Vault checking account |
| `accountId` (CC) | Vault card accounts (master/visa) |

### Risks

- Trial expires ~2026-03-21 — must validate integration works before then
- Post-trial data refresh uncertain — if it stops, API access becomes stale
- R$ 2,500/month not viable for personal use
- **Fallback**: MeuPluggy spreadsheet export + automated CSV import into Vault
