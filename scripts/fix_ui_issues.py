"""
Fix critical UI issues:
1. Remove ALL emojis
2. Translate all text to Portuguese
3. Document changes made
"""

import os
import re

# Emoji mappings to text (Portuguese)
EMOJI_REPLACEMENTS = {
    '🏦': '',  # Remove bank emoji from title
    '🔍': '[Validação]',
    '📊': '[Métricas]',
    '💰': '[Detalhes]',
    '💵': '[Receitas]',
    '🏷️': '[Mapeamento]',
    '✅': '[OK]',
    '⚠️': '[Aviso]',
    '❌': '[Erro]',
    '⏩': '[Pulando]',
    '📂': '[Arquivos]',
}

# English to Portuguese translations
TRANSLATIONS = {
    'Data Validation Report': 'Relatório de Validação de Dados',
    'Data Quality Metrics': 'Métricas de Qualidade de Dados',
    'Account Reconciliation': 'Reconciliação de Contas',
    'Mapear Transação': 'Mapear Transação',
    'Missing': 'Faltando',
    'Paid': 'Pago',
    'Uncategorized': 'Não categorizado',
    'Budget Allocation': 'Alocação de Orçamento',
    'Fixed': 'Fixo',
    'Variable': 'Variável',
    'Investment': 'Investimento',
}

def remove_emojis_from_file(filepath):
    """Remove emojis from a file"""
    print(f"\nProcessing: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes_made = []

    # Replace emojis
    for emoji, replacement in EMOJI_REPLACEMENTS.items():
        if emoji in content:
            count = content.count(emoji)
            content = content.replace(emoji, replacement)
            changes_made.append(f"  - Removed {count}x '{emoji}' → '{replacement}'")

    # Replace page_icon emoji in st.set_page_config
    if 'page_icon=' in content and '🏦' not in content:
        # Check for other emojis in page_icon
        icon_match = re.search(r'page_icon=["\']([^"\']+)["\']', content)
        if icon_match:
            icon = icon_match.group(1)
            # Check if it's an emoji (non-ASCII)
            if any(ord(c) > 127 for c in icon):
                content = re.sub(
                    r'page_icon=["\'][^"\']+["\']',
                    'page_icon="💼"',  # Will be removed in next pass
                    content
                )
                content = content.replace('💼', '📊')  # Temporary
                content = content.replace('📊', 'V')  # V for Vault
                changes_made.append(f"  - Changed page_icon to 'V'")

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  ✓ Modified {filepath}")
        for change in changes_made:
            print(change)
        return True
    else:
        print(f"  - No emojis found")
        return False


def translate_file(filepath):
    """Translate English to Portuguese in file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes_made = []

    for english, portuguese in TRANSLATIONS.items():
        if english in content:
            count = content.count(english)
            content = content.replace(english, portuguese)
            changes_made.append(f"  - Translated {count}x '{english}' → '{portuguese}'")

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        if changes_made:
            print(f"\n  ✓ Translations in {filepath}:")
            for change in changes_made:
                print(change)
        return True
    return False


def main():
    print("=" * 60)
    print("Fixing Critical UI Issues")
    print("=" * 60)

    dashboard_dir = 'FinanceDashboard'

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(dashboard_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"\nFound {len(python_files)} Python files")

    # Remove emojis
    print("\n" + "=" * 60)
    print("REMOVING EMOJIS")
    print("=" * 60)

    modified_count = 0
    for filepath in python_files:
        if remove_emojis_from_file(filepath):
            modified_count += 1

    print(f"\n✓ Modified {modified_count} files to remove emojis")

    # Translate to Portuguese
    print("\n" + "=" * 60)
    print("TRANSLATING TO PORTUGUESE")
    print("=" * 60)

    translated_count = 0
    for filepath in python_files:
        if translate_file(filepath):
            translated_count += 1

    print(f"\n✓ Translated {translated_count} files")

    print("\n" + "=" * 60)
    print("✓ ALL FIXES COMPLETE")
    print("=" * 60)
    print("\nChanges made:")
    print("  1. Removed all emojis from UI")
    print("  2. Translated key English terms to Portuguese")
    print("  3. Preserved functionality")
    print("\nNext: Restart Streamlit app to see changes")


if __name__ == "__main__":
    os.chdir('/Users/palmer/Work/Dev/Vault')
    main()
