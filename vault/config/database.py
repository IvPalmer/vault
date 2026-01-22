"""
Database configuration for THE VAULT
Uses environment variables with fallback defaults
"""

import os

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('VAULT_DB_HOST', 'localhost'),
    'port': os.getenv('VAULT_DB_PORT', '5432'),
    'database': os.getenv('VAULT_DB_NAME', 'vault_finance'),
    'user': os.getenv('VAULT_DB_USER', 'palmer'),
    'password': os.getenv('VAULT_DB_PASSWORD', ''),  # Empty for local trust auth
}

# Connection pool settings
POOL_MIN_CONNECTIONS = int(os.getenv('VAULT_POOL_MIN', '1'))
POOL_MAX_CONNECTIONS = int(os.getenv('VAULT_POOL_MAX', '10'))
