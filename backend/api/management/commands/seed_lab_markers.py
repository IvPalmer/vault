"""Seed LabMarker records from the comprehensive panels.

Mirrors the data structures in:
  - vault/src/components/saude/palmerHealthData.js (PALMER_LAB_PANEL)
  - vault/src/components/saude/rafaHealthData.js (RAFA_LAB_PANEL)

Each marker is attached to the matching HealthExam (by data_coleta).
Idempotent — uses get_or_create on (exam, category_slug, key).

Run after seed_health to ensure exams exist:
    python manage.py seed_health
    python manage.py seed_lab_markers
"""
from datetime import date
from decimal import Decimal
from django.core.management.base import BaseCommand
from api.models import Profile, HealthExam, LabMarker


def D(v):
    """Convert numeric value to Decimal, None for None/non-numeric."""
    if v is None:
        return None
    if isinstance(v, str):
        return None
    return Decimal(str(v))


# ─── PALMER PANEL — collected 2025-05-28 by DASA ────────────────────
# Inflammatory markers re-collected 2026-04-28 (PCR + VHS normalized)
PALMER_BASELINE_DATE = date(2025, 4, 15)  # matches seed_health "Painel laboratorial completo"
PALMER_FOLLOWUP_DATE = date(2026, 4, 28)  # matches seed_health "Follow-up PCR + VHS"

PALMER_CATEGORIES = [
    {
        'slug': 'hemograma', 'label': 'Hemograma', 'order': 1,
        'exam_date': PALMER_BASELINE_DATE,
        'markers': [
            {'key': 'hemoglobina', 'label': 'Hemoglobina', 'value': 15.7, 'unit': 'g/dL', 'ref_min': 12, 'ref_max': 16, 'status': 'normal'},
            {'key': 'hematocrito', 'label': 'Hematócrito', 'value': 46.3, 'unit': '%', 'ref_min': 36, 'ref_max': 46, 'status': 'limite_superior'},
            {'key': 'leucocitos', 'label': 'Leucócitos', 'value': 6020, 'unit': '/µL', 'ref_min': 4500, 'ref_max': 11000, 'status': 'normal'},
            {'key': 'plaquetas', 'label': 'Plaquetas', 'value': 262000, 'unit': '/µL', 'ref_min': 150000, 'ref_max': 400000, 'status': 'normal'},
        ],
    },
    {
        'slug': 'glicemico', 'label': 'Metabolismo glicêmico', 'order': 2,
        'exam_date': PALMER_BASELINE_DATE,
        'markers': [
            {'key': 'glicose', 'label': 'Glicemia jejum', 'value': 86, 'unit': 'mg/dL', 'ref_min': 70, 'ref_max': 100, 'status': 'normal'},
            {'key': 'hba1c', 'label': 'HbA1c', 'value': 4.8, 'unit': '%', 'ref_max': 5.7, 'status': 'normal'},
            {'key': 'homa_ir', 'label': 'HOMA-IR', 'value': 1.65, 'unit': '', 'ref_max': 2, 'status': 'normal'},
        ],
    },
    {
        'slug': 'lipidios', 'label': 'Perfil lipídico', 'order': 3,
        'exam_date': PALMER_BASELINE_DATE,
        'markers': [
            {'key': 'colesterol_total', 'label': 'Colesterol total', 'value': 247, 'unit': 'mg/dL', 'ref_max': 190, 'status': 'alto'},
            {'key': 'ldl', 'label': 'LDL', 'value': 176, 'unit': 'mg/dL', 'ref_max': 130, 'status': 'alto'},
            {'key': 'apo_b', 'label': 'Apo B', 'value': 135, 'unit': 'mg/dL', 'ref_min': 66, 'ref_max': 133, 'status': 'alto',
             'obs': 'Marcador mais preciso de risco cardiovascular que LDL isolado'},
            {'key': 'fibrinogenio', 'label': 'Fibrinogênio', 'value': 380, 'unit': 'mg/dL', 'ref_min': 200, 'ref_max': 400, 'status': 'limite_superior'},
        ],
    },
    {
        'slug': 'tireoide', 'label': 'Função tireoide', 'order': 4,
        'exam_date': PALMER_BASELINE_DATE,
        'markers': [
            {'key': 'tsh', 'label': 'TSH', 'value': 2.02, 'unit': 'mIU/L', 'ref_min': 0.4, 'ref_max': 4, 'status': 'normal'},
            {'key': 't4_livre', 'label': 'T4 livre', 'value': 1.0, 'unit': 'ng/dL', 'ref_min': 0.93, 'ref_max': 1.7, 'status': 'normal'},
            {'key': 'anti_tpo', 'label': 'Anti-TPO', 'value': 11, 'unit': 'UI/mL', 'ref_max': 35, 'status': 'normal'},
        ],
    },
    {
        'slug': 'adrenal', 'label': 'Eixo adrenal', 'order': 5,
        'exam_date': PALMER_BASELINE_DATE,
        'markers': [
            {'key': 'cortisol_am', 'label': 'Cortisol matinal', 'value': 5, 'unit': 'µg/dL', 'ref_min': 6.2, 'ref_max': 18, 'status': 'baixo',
             'obs': 'Baixo — investigar fadiga adrenal/insuficiência. Repetir em jejum, 8h da manhã.'},
        ],
    },
    {
        'slug': 'renal', 'label': 'Função renal', 'order': 6,
        'exam_date': PALMER_BASELINE_DATE,
        'markers': [
            {'key': 'creatinina', 'label': 'Creatinina', 'value': 1.07, 'unit': 'mg/dL', 'ref_min': 0.6, 'ref_max': 1.2, 'status': 'normal'},
            {'key': 'egfr', 'label': 'eGFR', 'value': 90, 'unit': 'mL/min/1.73m²', 'ref_min': 90, 'status': 'normal',
             'ref_text': '> 90 mL/min/1.73m² — função preservada'},
            {'key': 'ureia', 'label': 'Uréia', 'value': 34, 'unit': 'mg/dL', 'ref_min': 15, 'ref_max': 45, 'status': 'normal'},
        ],
    },
    {
        'slug': 'hepatica', 'label': 'Função hepática', 'order': 7,
        'exam_date': PALMER_BASELINE_DATE,
        'markers': [
            {'key': 'tgo', 'label': 'TGO/AST', 'value': 29, 'unit': 'U/L', 'ref_max': 33, 'status': 'normal'},
            {'key': 'tgp', 'label': 'TGP/ALT', 'value': 26, 'unit': 'U/L', 'ref_max': 32, 'status': 'normal'},
            {'key': 'ggt', 'label': 'GGT', 'value': 19, 'unit': 'U/L', 'ref_max': 55, 'status': 'normal'},
            {'key': 'fa', 'label': 'Fosfatase alcalina', 'value': 96, 'unit': 'U/L', 'ref_min': 30, 'ref_max': 120, 'status': 'normal'},
        ],
    },
    {
        'slug': 'inflamatorio', 'label': 'Marcadores inflamatórios', 'order': 8,
        'exam_date': PALMER_FOLLOWUP_DATE,  # most recent values
        'markers': [
            {'key': 'pcr', 'label': 'PCR ultrassensível', 'value': 0.25, 'unit': 'mg/dL', 'ref_max': 0.5, 'status': 'normal',
             'obs': 'Normalizou — caiu 13× desde mai/2025. Resolução do processo inflamatório sistêmico.'},
            {'key': 'vhs', 'label': 'VHS', 'value': 14, 'unit': 'mm/h', 'ref_max': 15, 'status': 'normal',
             'obs': 'Dentro da referência. Caiu de 17 (mai/2025).'},
        ],
    },
    {
        'slug': 'coagulacao', 'label': 'Coagulação', 'order': 9,
        'exam_date': PALMER_BASELINE_DATE,
        'markers': [
            {'key': 'tp', 'label': 'TP', 'value': 12.7, 'unit': 's', 'status': 'normal'},
            {'key': 'inr', 'label': 'INR', 'value': 1.0, 'unit': '', 'ref_min': 0.8, 'ref_max': 1.2, 'status': 'normal'},
            {'key': 'ttpa', 'label': 'TTPA', 'value': 37.7, 'unit': 's', 'status': 'normal'},
            {'key': 'd_dimero', 'label': 'D-dímero', 'value': 120, 'unit': 'ng/mL', 'ref_max': 500, 'status': 'normal'},
        ],
    },
    {
        'slug': 'especificos', 'label': 'Marcadores específicos', 'order': 10,
        'exam_date': PALMER_BASELINE_DATE,
        'markers': [
            {'key': 'g6pd', 'label': 'G6PD', 'value': 2.1, 'unit': 'U/g Hb', 'ref_min': 6.7, 'status': 'baixo',
             'ref_text': '> 6.7 normal · 2.2-6.7 intermediário · < 2.2 deficiente',
             'obs': 'Deficiência confirmada (Classe III WHO). Evitar gatilhos hemolíticos.'},
            {'key': 'vit_d', 'label': 'Vitamina D (25-OH)', 'value': 36.6, 'unit': 'ng/mL', 'ref_min': 30, 'ref_max': 100, 'status': 'normal'},
        ],
    },
]


# ─── RAFA PANEL — collected 2025-05-01 by DASA ──────────────────────
RAFA_BASELINE_DATE = date(2025, 5, 1)  # matches seed_health "Hemograma — Consolidado"

RAFA_CATEGORIES = [
    {
        'slug': 'hemograma', 'label': 'Hemograma', 'order': 1,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'hemacias', 'label': 'Hemácias', 'value': 4.59, 'unit': 'milhões/µL', 'ref_min': 3.8, 'ref_max': 4.8, 'status': 'normal'},
            {'key': 'hemoglobina', 'label': 'Hemoglobina', 'value': 14.6, 'unit': 'g/dL', 'ref_min': 12.0, 'ref_max': 15.0, 'status': 'normal'},
            {'key': 'hematocrito', 'label': 'Hematócrito', 'value': 42.8, 'unit': '%', 'ref_min': 36.0, 'ref_max': 46.0, 'status': 'normal'},
            {'key': 'vcm', 'label': 'VCM', 'value': 93.3, 'unit': 'fL', 'ref_min': 83, 'ref_max': 101, 'status': 'normal'},
            {'key': 'hcm', 'label': 'HCM', 'value': 31.8, 'unit': 'pg', 'ref_min': 27, 'ref_max': 32, 'status': 'normal'},
            {'key': 'chcm', 'label': 'CHCM', 'value': 34.1, 'unit': 'g/dL', 'ref_min': 31, 'ref_max': 35, 'status': 'normal'},
            {'key': 'rdw', 'label': 'RDW', 'value': 13.0, 'unit': '%', 'ref_min': 11.6, 'ref_max': 14.0, 'status': 'normal'},
            {'key': 'leucocitos', 'label': 'Leucócitos', 'value': 7470, 'unit': '/µL', 'ref_min': 4000, 'ref_max': 10000, 'status': 'normal'},
            {'key': 'linfocitos', 'label': 'Linfócitos', 'value': 30.6, 'unit': '%', 'ref_min': 20, 'ref_max': 40, 'status': 'normal'},
            {'key': 'monocitos', 'label': 'Monócitos', 'value': 7.9, 'unit': '%', 'ref_min': 2.0, 'ref_max': 10.0, 'status': 'normal'},
            {'key': 'eosinofilos', 'label': 'Eosinófilos', 'value': 3.0, 'unit': '%', 'ref_min': 1.0, 'ref_max': 6.0, 'status': 'normal'},
            {'key': 'basofilos', 'label': 'Basófilos', 'value': 0.6, 'unit': '%', 'ref_min': 0, 'ref_max': 2.0, 'status': 'normal'},
            {'key': 'plaquetas', 'label': 'Plaquetas', 'value': 464000, 'unit': '/µL', 'ref_min': 150000, 'ref_max': 450000, 'status': 'alto',
             'obs': 'Trombocitose leve (acima de 450k). Geralmente reativa — monitorar na gestação.'},
            {'key': 'vpm', 'label': 'VPM', 'value': 9.7, 'unit': 'fL', 'ref_min': 9.2, 'ref_max': 12.8, 'status': 'normal'},
        ],
    },
    {
        'slug': 'glicemico', 'label': 'Metabolismo glicêmico', 'order': 2,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'glicose', 'label': 'Glicemia jejum', 'value': 81, 'unit': 'mg/dL', 'ref_min': 70, 'ref_max': 99, 'status': 'normal'},
            {'key': 'hba1c', 'label': 'HbA1c', 'value': 5.1, 'unit': '%', 'ref_max': 5.7, 'status': 'normal',
             'obs': '2024 estava 5.7% (limite pré-DM). Normalizou em 2025.'},
            {'key': 'insulina', 'label': 'Insulina', 'value': 5.3, 'unit': 'µUI/mL', 'ref_min': 2.5, 'ref_max': 13.1, 'status': 'normal'},
            {'key': 'homa_ir', 'label': 'HOMA-IR', 'value': 1.06, 'unit': '', 'ref_max': 2.7, 'status': 'normal'},
        ],
    },
    {
        'slug': 'lipidios', 'label': 'Perfil lipídico', 'order': 3,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'colesterol_total', 'label': 'Colesterol total', 'value': 223, 'unit': 'mg/dL', 'ref_max': 190, 'status': 'alto',
             'obs': 'Limítrofe alto. Aumento fisiológico esperado durante gestação (placenta).'},
            {'key': 'hdl', 'label': 'HDL', 'value': 62, 'unit': 'mg/dL', 'ref_min': 40, 'status': 'normal'},
            {'key': 'ldl', 'label': 'LDL', 'value': 143, 'unit': 'mg/dL', 'ref_max': 130, 'status': 'limite_superior'},
            {'key': 'trigliceres', 'label': 'Triglicérides', 'value': 74, 'unit': 'mg/dL', 'ref_max': 150, 'status': 'normal'},
            {'key': 'apo_a', 'label': 'Apo A', 'value': 162, 'unit': 'mg/dL', 'ref_min': 108, 'ref_max': 225, 'status': 'normal'},
            {'key': 'apo_b', 'label': 'Apo B', 'value': 103, 'unit': 'mg/dL', 'ref_min': 60, 'ref_max': 117, 'status': 'normal'},
            {'key': 'lp_a', 'label': 'Lipoproteína(a)', 'value': 29.7, 'unit': 'nmol/L', 'ref_max': 75, 'status': 'normal'},
        ],
    },
    {
        'slug': 'tireoide', 'label': 'Função tireoide', 'order': 4,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'tsh', 'label': 'TSH', 'value': 0.96, 'unit': 'µUI/mL', 'ref_min': 0.40, 'ref_max': 4.30, 'status': 'normal',
             'obs': 'Janela TSH gestacional 1º tri ideal: <2.5 — atual está adequado'},
            {'key': 't4_livre', 'label': 'T4 livre', 'value': 1.13, 'unit': 'ng/dL', 'ref_min': 0.93, 'ref_max': 1.70, 'status': 'normal'},
            {'key': 'anti_tpo', 'label': 'Anti-TPO', 'value': 11.1, 'unit': 'UI/mL', 'ref_max': 35, 'status': 'normal'},
            {'key': 'anti_tg', 'label': 'Anti-tireoglobulina', 'value': 17.6, 'unit': 'UI/mL', 'ref_max': 115, 'status': 'normal'},
        ],
    },
    {
        'slug': 'micronutrientes', 'label': 'Ferro / vitaminas pré-natal', 'order': 5,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'ferro', 'label': 'Ferro sérico', 'value': 110, 'unit': 'µg/dL', 'ref_min': 33, 'ref_max': 193, 'status': 'normal'},
            {'key': 'ferritina', 'label': 'Ferritina', 'value': 33.8, 'unit': 'ng/mL', 'ref_min': 13, 'ref_max': 150, 'status': 'normal',
             'obs': 'Ideal pré-gestacional > 30. Reservas adequadas.'},
            {'key': 'transferrina', 'label': 'Transferrina', 'value': 286, 'unit': 'mg/dL', 'ref_min': 200, 'ref_max': 360, 'status': 'normal'},
            {'key': 'b12', 'label': 'Vitamina B-12', 'value': 609, 'unit': 'pg/mL', 'ref_min': 245, 'ref_max': 985, 'status': 'normal'},
            {'key': 'folato', 'label': 'Ácido fólico', 'value': 23.6, 'unit': 'ng/mL', 'ref_min': 5.38, 'status': 'normal',
             'obs': 'Crítico na gestação para tubo neural — níveis ótimos.'},
            {'key': 'homocisteina', 'label': 'Homocisteína', 'value': 5.53, 'unit': 'µmol/L', 'ref_min': 4.44, 'ref_max': 13.56, 'status': 'normal'},
            {'key': 'vit_d', 'label': '25-OH Vitamina D', 'value': 40.8, 'unit': 'ng/mL', 'ref_min': 30, 'ref_max': 60, 'status': 'normal'},
        ],
    },
    {
        'slug': 'renal', 'label': 'Função renal e eletrólitos', 'order': 6,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'creatinina', 'label': 'Creatinina', 'value': 0.68, 'unit': 'mg/dL', 'ref_min': 0.50, 'ref_max': 1.00, 'status': 'normal'},
            {'key': 'sodio', 'label': 'Sódio', 'value': 137, 'unit': 'mmol/L', 'ref_min': 136, 'ref_max': 145, 'status': 'normal'},
            {'key': 'potassio', 'label': 'Potássio', 'value': 4.9, 'unit': 'mmol/L', 'ref_min': 3.5, 'ref_max': 5.1, 'status': 'normal'},
            {'key': 'calcio', 'label': 'Cálcio total', 'value': 9.7, 'unit': 'mg/dL', 'ref_min': 8.6, 'ref_max': 10.0, 'status': 'normal'},
            {'key': 'fosforo', 'label': 'Fósforo', 'value': 4.2, 'unit': 'mg/dL', 'ref_min': 2.5, 'ref_max': 4.5, 'status': 'normal'},
        ],
    },
    {
        'slug': 'hepatica', 'label': 'Função hepática', 'order': 7,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'tgo', 'label': 'TGO/AST', 'value': 20, 'unit': 'U/L', 'ref_max': 32, 'status': 'normal'},
            {'key': 'tgp', 'label': 'TGP/ALT', 'value': 21, 'unit': 'U/L', 'ref_max': 33, 'status': 'normal'},
            {'key': 'ggt', 'label': 'Gama-GT', 'value': 13, 'unit': 'U/L', 'ref_max': 40, 'status': 'normal'},
            {'key': 'fa', 'label': 'Fosfatase alcalina', 'value': 43, 'unit': 'U/L', 'ref_min': 35, 'ref_max': 105, 'status': 'normal'},
            {'key': 'ptn_total', 'label': 'Proteínas totais', 'value': 7.9, 'unit': 'g/dL', 'ref_min': 6.4, 'ref_max': 8.3, 'status': 'normal'},
            {'key': 'albumina', 'label': 'Albumina', 'value': 5.1, 'unit': 'g/dL', 'ref_min': 3.5, 'ref_max': 5.2, 'status': 'normal'},
        ],
    },
    {
        'slug': 'hormonios_sexuais', 'label': 'Hormônios sexuais (pré-gestacional)', 'order': 8,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'estradiol', 'label': 'Estradiol', 'value': 261, 'unit': 'pg/mL', 'status': 'normal',
             'obs': 'Depende fase ciclo — coleta sem fase informada'},
            {'key': 'fsh', 'label': 'FSH', 'value': 5.4, 'unit': 'mUI/mL', 'status': 'normal'},
            {'key': 'prolactina', 'label': 'Prolactina', 'value': 13.2, 'unit': 'ng/mL', 'ref_min': 4.8, 'ref_max': 23.3, 'status': 'normal'},
            {'key': 'testo_total', 'label': 'Testosterona total', 'value': 28.3, 'unit': 'ng/dL', 'status': 'normal'},
        ],
    },
    {
        'slug': 'coagulacao', 'label': 'Coagulação', 'order': 9,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'd_dimero', 'label': 'D-dímero', 'value': 220, 'unit': 'ng/mL FEU', 'ref_max': 500, 'status': 'normal',
             'obs': 'Aumenta fisiologicamente na gestação — basal pré-gestacional.'},
        ],
    },
    {
        'slug': 'adrenal', 'label': 'Eixo adrenal', 'order': 10,
        'exam_date': RAFA_BASELINE_DATE,
        'markers': [
            {'key': 'cortisol_am', 'label': 'Cortisol matinal', 'value': 8.0, 'unit': 'µg/dL', 'ref_min': 6.2, 'ref_max': 18.0, 'status': 'normal'},
        ],
    },
]


def populate_profile(stdout, profile, categories):
    """Create LabMarker entries for a profile from a categories list."""
    created_total = 0
    skipped = 0
    missing_exams = set()

    for cat in categories:
        cat_slug = cat['slug']
        cat_label = cat['label']
        cat_order = cat['order']
        exam_date = cat['exam_date']

        # Find the exam by profile + date
        try:
            exam = HealthExam.objects.filter(profile=profile, data=exam_date).first()
            if not exam:
                missing_exams.add(str(exam_date))
                continue
        except HealthExam.DoesNotExist:
            missing_exams.add(str(exam_date))
            continue

        for i, m in enumerate(cat['markers']):
            obj, created = LabMarker.objects.get_or_create(
                exam=exam,
                category_slug=cat_slug,
                key=m['key'],
                defaults={
                    'profile': profile,
                    'category_label': cat_label,
                    'category_order': cat_order,
                    'label': m['label'],
                    'order': i,
                    'value': D(m.get('value')),
                    'value_text': m.get('value_text', ''),
                    'unit': m.get('unit', ''),
                    'ref_min': D(m.get('ref_min')),
                    'ref_max': D(m.get('ref_max')),
                    'ref_text': m.get('ref_text', ''),
                    'status': m.get('status', 'normal'),
                    'obs': m.get('obs', ''),
                },
            )
            if created:
                created_total += 1
            else:
                skipped += 1

    stdout.write(f'  {profile.name}: +{created_total} created · {skipped} existing')
    if missing_exams:
        stdout.write(f'  WARN: missing exams for dates: {sorted(missing_exams)}')


class Command(BaseCommand):
    help = 'Seed LabMarker records from PALMER + RAFA panels'

    def handle(self, *args, **opts):
        try:
            palmer = Profile.objects.get(name='Palmer')
        except Profile.DoesNotExist:
            self.stderr.write('Profile "Palmer" not found.')
            return
        try:
            rafa = Profile.objects.get(name='Rafa')
        except Profile.DoesNotExist:
            self.stderr.write('Profile "Rafa" not found.')
            return

        self.stdout.write('Seeding lab markers…')
        populate_profile(self.stdout, palmer, PALMER_CATEGORIES)
        populate_profile(self.stdout, rafa, RAFA_CATEGORIES)
        self.stdout.write(self.style.SUCCESS('Done.'))
