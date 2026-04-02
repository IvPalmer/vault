"""
Pluggy Open Finance API client.

Thin wrapper around Pluggy REST API for pulling Brazilian bank data.
Credentials loaded from Django settings / environment variables.
"""

import logging
import time

import requests

logger = logging.getLogger(__name__)

BASE_URL = 'https://api.pluggy.ai'


class PluggyClient:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self._api_key = None
        self._api_key_expires = 0

    def _authenticate(self):
        """Get API key (cached for 1.5h, expires at 2h)."""
        if self._api_key and time.time() < self._api_key_expires:
            return self._api_key

        resp = requests.post(f'{BASE_URL}/auth', json={
            'clientId': self.client_id,
            'clientSecret': self.client_secret,
        }, timeout=30)
        resp.raise_for_status()
        self._api_key = resp.json()['apiKey']
        self._api_key_expires = time.time() + 5400  # 1.5h
        logger.info('Pluggy: authenticated successfully')
        return self._api_key

    def _headers(self):
        return {
            'X-API-KEY': self._authenticate(),
            'Content-Type': 'application/json',
        }

    def get_item(self, item_id):
        """Get connection (Item) status."""
        resp = requests.get(f'{BASE_URL}/items/{item_id}',
                            headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def update_item(self, item_id, wait=True, timeout=120, poll_interval=5):
        """
        Trigger a data refresh for an Item (re-fetches from the bank).

        Args:
            item_id: Pluggy item UUID
            wait: if True, poll until status is UPDATED or error
            timeout: max seconds to wait
            poll_interval: seconds between polls

        Returns: final item dict
        """
        resp = requests.patch(f'{BASE_URL}/items/{item_id}',
                              json={}, headers=self._headers(), timeout=30)
        if resp.status_code == 400:
            body = resp.json()
            msg = body.get('message', '') or body.get('codeDescription', '')
            if 'ITEM_ALREADY_UPDATING' in msg or body.get('codeDescription') == 'ITEM_ALREADY_UPDATING':
                # Already refreshing, just poll for completion
                logger.info('Pluggy: item already updating, waiting...')
                item = self.get_item(item_id)
            elif 'MeuPluggy' in msg:
                # MeuPluggy items refresh on their own schedule
                logger.info('Pluggy: MeuPluggy item — skipping manual refresh.')
                return self.get_item(item_id)
            else:
                resp.raise_for_status()
        elif resp.status_code == 403:
            # Post-trial: refresh blocked, but reads still work via MeuPluggy
            logger.warning(
                'Pluggy: refresh blocked (trial expired). '
                'Data is still synced daily by MeuPluggy.')
            return self.get_item(item_id)
        else:
            resp.raise_for_status()
            item = resp.json()

        if not wait:
            return item

        start = time.time()
        while time.time() - start < timeout:
            status = item.get('status')
            if status in ('UPDATED', 'LOGIN_ERROR', 'OUTDATED'):
                return item
            exec_status = item.get('executionStatus')
            if exec_status == 'ERROR':
                return item
            time.sleep(poll_interval)
            item = self.get_item(item_id)

        return item

    def get_accounts(self, item_id):
        """List all accounts for an Item."""
        resp = requests.get(f'{BASE_URL}/accounts',
                            params={'itemId': item_id},
                            headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()['results']

    def get_transactions(self, account_id, from_date, to_date, page_size=500):
        """
        Fetch all transactions for an account in a date range.
        Handles pagination automatically.

        Args:
            account_id: Pluggy account UUID
            from_date: 'YYYY-MM-DD' start date
            to_date: 'YYYY-MM-DD' end date
            page_size: results per page (max 500)

        Returns: list of transaction dicts
        """
        all_txns = []
        page = 1
        while True:
            resp = requests.get(f'{BASE_URL}/transactions', params={
                'accountId': account_id,
                'from': from_date,
                'to': to_date,
                'pageSize': page_size,
                'page': page,
            }, headers=self._headers(), timeout=60)
            resp.raise_for_status()
            data = resp.json()
            results = data.get('results', [])
            all_txns.extend(results)

            total_pages = data.get('totalPages', 1)
            if page >= total_pages:
                break
            page += 1

        return all_txns

    def get_bills(self, account_id):
        """Get credit card bills for an account. Returns list of bill dicts."""
        resp = requests.get(f'{BASE_URL}/bills',
                            params={'accountId': account_id},
                            headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json().get('results', [])

    def get_account_balance(self, account_id):
        """Get current balance for a single account."""
        resp = requests.get(f'{BASE_URL}/accounts/{account_id}',
                            headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return {
            'balance': data.get('balance'),
            'currencyCode': data.get('currencyCode'),
            'name': data.get('name'),
            'type': data.get('type'),
            'subtype': data.get('subtype'),
            'creditData': data.get('creditData'),
        }
