"""Seed initial health data:
  - Palmer: hip investigation exams, G6PD, recent labs
  - Rafa: 3 hemogramas (2024 + 2025)
  - Active pregnancy: confirmed 2026-05-02

Idempotent — safe to re-run.
"""
from datetime import date
from django.core.management.base import BaseCommand
from api.models import Profile, HealthExam, Pregnancy


PALMER_EXAMS = [
    {
        'tipo': 'imagem_ct',
        'nome': 'Tomografia computadorizada do quadril',
        'data': date(2025, 9, 12),
        'arquivo_path': 'Plano de Saude/Amil/../laudos/quadril_ct.pdf',
        'notes': 'Achados: morfologia tipo CAM com α-angle elevado lateral. Entesopatia AIIS. '
                 'Base do estudo de imagem do quadril esquerdo.',
        'valores': {
            'alpha_angle_lateral_deg': 68,
            'lcea_deg': 36,
            'morfologia': 'CAM-type FAI',
        },
    },
    {
        'tipo': 'genetico',
        'nome': 'G6PD — quantitativa',
        'data': date(2024, 8, 14),
        'notes': 'Deficiência de G6PD confirmada. Padrão X-recessivo. Evitar gatilhos hemolíticos.',
        'valores': {
            'g6pd_atividade': 'reduzida',
            'classificacao_who': 'Classe III',
        },
    },
    {
        'tipo': 'densitometria',
        'nome': 'Densitometria corpo inteiro',
        'data': date(2024, 8, 14),
        'arquivo_path': 'Plano de Saude/../densitometria_corpo_inteiro.pdf',
        'notes': 'Composição corporal + densidade óssea.',
        'valores': {},
    },
    {
        'tipo': 'bioquimica',
        'nome': 'Painel laboratorial completo',
        'data': date(2025, 4, 15),
        'notes': 'PCR elevada — investigação inflamatória do quadril.',
        'valores': {
            'pcr_mg_l': '↑',
            'glicemia': 'normal',
            'tsh': 'normal',
        },
    },
    {
        'tipo': 'bioquimica',
        'nome': 'Follow-up PCR + VHS',
        'data': date(2026, 4, 28),
        'arquivo_path': 'Downloads/Laudo Completo 28_04_2026.pdf',
        'laboratorio': 'DASA',
        'medico': 'Dra. Valeria Nogueira Naves',
        'notes': 'Normalização — PCR 3.24 → 0.25 mg/dL (13× redução), VHS 17 → 14 mm/h. Processo inflamatório sistêmico resolvido em ~11 meses.',
        'valores': {
            'pcr_mg_dl': 0.25,
            'pcr_status': 'normal',
            'vhs_mm_h': 14,
            'vhs_status': 'normal',
            'vs_anterior_pcr': '3.24 (mai/2025)',
            'vs_anterior_vhs': '17 (mai/2025)',
        },
    },
]

RAFA_EXAMS = [
    {
        'tipo': 'hemograma',
        'nome': 'Hemograma Completo',
        'data': date(2024, 1, 1),
        'arquivo_path': 'Exames/2024/Rafaella - Hemograma Completo 2024.pdf',
        'valores': {},
        'notes': 'Hemograma basal pré-gestacional.',
    },
    {
        'tipo': 'hemograma',
        'nome': 'Hemograma',
        'data': date(2025, 5, 1),
        'arquivo_path': 'Exames/2025/Rafaella - Hemograma 05-2025.pdf',
        'valores': {},
        'notes': 'Hemograma controle.',
    },
    {
        'tipo': 'hemograma',
        'nome': 'Hemograma — Consolidado',
        'data': date(2025, 5, 1),
        'arquivo_path': 'Exames/2025/Rafaella - Hemograma 05-2025 Consolidado.pdf',
        'valores': {},
        'notes': 'Consolidado do laboratório.',
    },
    # ─── 1ª consulta pré-natal (2026-05-05) ───
    {
        'tipo': 'outro',
        'nome': '1ª consulta pré-natal',
        'data': date(2026, 5, 5),
        'medico': 'Dra. Nahara Alves Gomes Torres (CRM-DF 18529)',
        'laboratorio': 'Grupo Elas — Setor Sudoeste, Brasília',
        'arquivo_path': 'family/pregnancy/consultas/2026-05-05_1a_consulta/',
        'checkpoint_id': '1a-consulta',
        'notes': 'CID Z34.9. IG ~5+5. Solicitou painel laboratorial 1º tri completo (14 exames) + USG transvaginal gestacional. Receituário: Ogestan-Pré 1×/dia + sintomáticos. Frequência consultas: mensal até 32-34s, quinzenal 34-37s, semanal 37s-parto.',
        'valores': {
            'ig_consulta': '5+5',
            'cid': 'Z34.9',
            'pedidos_lab_count': 14,
            'pedidos_imagem': ['USG transvaginal gestacional'],
        },
    },
    # ─── Painel laboratorial 1º tri (coletado 2026-05-06) ───
    {
        'tipo': 'bioquimica',
        'nome': 'Painel laboratorial 1º trimestre',
        'data': date(2026, 5, 6),
        'medico': 'Dra. Nahara Alves Gomes Torres',
        'laboratorio': 'DASA / Lab Exame Asa Sul',
        'checkpoint_id': 'lab-1tri',
        'notes': 'Coleta em 06/05 com jejum 12h. 13 exames coletados; vitamina D aguardando autorização. Aguardando resultados.',
        'valores': {
            'status': 'coletado_aguardando_resultado',
            'jejum_horas': 12,
            'pendente_autorizacao': ['vitamina_d'],
            'painel': [
                'Tipagem sanguínea + Fator Rh + Coombs indireto',
                'Hemograma completo + Ferro + Ferritina',
                'Glicemia jejum + HbA1c + Insulina basal + HOMA-IR',
                'TSH + T4L',
                'Vitamina B12',
                'HIV', 'HTLV', 'VDRL',
                'HBsAg + Anti-HBs',
                'Anti-HCV',
                'Rubéola IgG/IgM',
                'Toxoplasmose IgG/IgM',
                'Citomegalovírus IgG/IgM',
                'EAS + Urocultura',
            ],
        },
    },
    # ─── USG transvaginal datação agendada (2026-05-18) ───
    {
        'tipo': 'imagem_us',
        'nome': 'USG transvaginal gestacional (datação)',
        'data': date(2026, 5, 18),
        'medico': 'Dra. Nahara Alves Gomes Torres (solicitante)',
        'laboratorio': 'A confirmar',
        'checkpoint_id': 'usg-datacao',
        'notes': 'Agendada 18/05/2026 (~IG 7+4). Coberta pela Proasa (carências aproveitadas) desde adesão 06/05. Amil USG libera apenas 28/05.',
        'valores': {
            'status': 'agendado',
            'cobertura': 'Proasa ADV 300 DF',
        },
    },
]


class Command(BaseCommand):
    help = 'Seed initial health data for Palmer + Rafa + active pregnancy'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Wipe existing health data first')

    def handle(self, *args, **opts):
        try:
            palmer = Profile.objects.get(name='Palmer')
        except Profile.DoesNotExist:
            self.stderr.write('Profile "Palmer" not found. Aborting.')
            return
        try:
            rafa = Profile.objects.get(name='Rafa')
        except Profile.DoesNotExist:
            self.stderr.write('Profile "Rafa" not found. Aborting.')
            return

        if opts['reset']:
            HealthExam.objects.filter(profile__in=[palmer, rafa]).delete()
            Pregnancy.objects.filter(titular=palmer, gestante=rafa).delete()
            self.stdout.write(self.style.WARNING('Existing health data wiped.'))

        # ── Pregnancy ──
        pregnancy, created = Pregnancy.objects.get_or_create(
            titular=palmer,
            gestante=rafa,
            confirmada_em=date(2026, 5, 2),
            defaults={
                'status': 'ativa',
                'notes': 'Primeira gestação. Detalhes operacionais em health/family/.',
                'plano_nome': 'Amil 702 PME (PRC 609)',
                'plano_vigencia_inicio': date(2026, 4, 28),  # confirmar dia exato
                'carencia_obstetrica_dias': 300,
                # Estimativa provisória — substituir quando USG datação confirmar.
                # IG estimada ~5 sem em 2026-05-02 → DUM ~28/03/2026, DPP ~02/01/2027
                'dum': date(2026, 3, 28),
                'dpp': date(2027, 1, 2),
            },
        )
        if not created:
            updated = False
            if not pregnancy.plano_nome:
                pregnancy.plano_nome = 'Amil 702 PME (PRC 609)'
                updated = True
            if not pregnancy.plano_vigencia_inicio:
                pregnancy.plano_vigencia_inicio = date(2026, 4, 28)
                updated = True
            if not pregnancy.dum:
                pregnancy.dum = date(2026, 3, 28)
                updated = True
            if not pregnancy.dpp:
                pregnancy.dpp = date(2027, 1, 2)
                updated = True
            if updated:
                pregnancy.save()
        action = 'Created' if created else 'Found existing'
        self.stdout.write(f'{action} pregnancy: {pregnancy}')

        # ── Palmer exams ──
        for spec in PALMER_EXAMS:
            obj, created = HealthExam.objects.get_or_create(
                profile=palmer,
                nome=spec['nome'],
                data=spec['data'],
                defaults={
                    'tipo': spec['tipo'],
                    'arquivo_path': spec.get('arquivo_path', ''),
                    'notes': spec.get('notes', ''),
                    'valores': spec.get('valores', {}),
                },
            )
            tag = '+' if created else '·'
            self.stdout.write(f'  {tag} Palmer: {obj.nome} ({obj.data})')

        # ── Rafa exams ──
        for spec in RAFA_EXAMS:
            defaults = {
                'tipo': spec['tipo'],
                'arquivo_path': spec.get('arquivo_path', ''),
                'notes': spec.get('notes', ''),
                'valores': spec.get('valores', {}),
                'medico': spec.get('medico', ''),
                'laboratorio': spec.get('laboratorio', ''),
                'checkpoint_id': spec.get('checkpoint_id', ''),
            }
            # Link pregnancy-related exams (consulta + future pre-natal exams)
            if spec.get('checkpoint_id'):
                defaults['pregnancy'] = pregnancy
            obj, created = HealthExam.objects.get_or_create(
                profile=rafa,
                nome=spec['nome'],
                data=spec['data'],
                defaults=defaults,
            )
            # If exam already exists but is missing checkpoint_id linkage, fill it in
            if not created and spec.get('checkpoint_id') and not obj.checkpoint_id:
                obj.checkpoint_id = spec['checkpoint_id']
                obj.pregnancy = pregnancy
                obj.medico = obj.medico or spec.get('medico', '')
                obj.laboratorio = obj.laboratorio or spec.get('laboratorio', '')
                obj.save()
            tag = '+' if created else '·'
            self.stdout.write(f'  {tag} Rafa: {obj.nome} ({obj.data})')

        self.stdout.write(self.style.SUCCESS('Done.'))
