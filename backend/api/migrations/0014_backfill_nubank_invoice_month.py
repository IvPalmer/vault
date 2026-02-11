"""
Backfill invoice_month, invoice_close_date, and invoice_payment_date for
existing NuBank credit card transactions that were imported without these fields.

The source_file field stores the original filename (e.g. "Nubank_2026-01-22.ofx").
We extract the closing date from it to derive invoice metadata.
"""
import re
from datetime import date

from django.db import migrations


def backfill_nubank_invoice_month(apps, schema_editor):
    Transaction = apps.get_model('api', 'Transaction')
    Account = apps.get_model('api', 'Account')

    # Find NuBank credit card accounts
    nubank_cc_accounts = Account.objects.filter(
        name__icontains='NuBank',
        account_type='credit_card',
    )

    if not nubank_cc_accounts.exists():
        return

    # Find transactions with empty invoice_month on these accounts
    txns = Transaction.objects.filter(
        account__in=nubank_cc_accounts,
        invoice_month='',
    )

    updated = 0
    for txn in txns.iterator():
        if not txn.source_file:
            continue

        match = re.search(r'Nubank_(\d{4})-(\d{2})-(\d{2})\.ofx', txn.source_file, re.IGNORECASE)
        if not match:
            continue

        inv_year = int(match.group(1))
        inv_month = int(match.group(2))
        inv_day = int(match.group(3))

        txn.invoice_month = f'{inv_year}-{inv_month:02d}'
        txn.invoice_close_date = date(inv_year, inv_month, inv_day)

        # Payment date: due_day (7) of the NEXT month after closing
        if inv_month == 12:
            pay_year = inv_year + 1
            pay_month = 1
        else:
            pay_year = inv_year
            pay_month = inv_month + 1
        txn.invoice_payment_date = date(pay_year, pay_month, 7)

        txn.save(update_fields=['invoice_month', 'invoice_close_date', 'invoice_payment_date'])
        updated += 1

    if updated:
        print(f'  Backfilled invoice_month for {updated} NuBank transactions')


def reverse_backfill(apps, schema_editor):
    Transaction = apps.get_model('api', 'Transaction')
    Account = apps.get_model('api', 'Account')

    nubank_cc_accounts = Account.objects.filter(
        name__icontains='NuBank',
        account_type='credit_card',
    )

    Transaction.objects.filter(
        account__in=nubank_cc_accounts,
        source_file__iregex=r'Nubank_\d{4}-\d{2}-\d{2}\.ofx',
    ).update(
        invoice_month='',
        invoice_close_date=None,
        invoice_payment_date=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_add_savings_target_to_profile'),
    ]

    operations = [
        migrations.RunPython(backfill_nubank_invoice_month, reverse_backfill),
    ]
