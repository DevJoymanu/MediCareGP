"""
Management command to set up demo data for testing the simplified UI.
Usage: python manage.py setup_demo
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from patients.models import Patient, MedicalAidPlanConfig, BiometricTemplate
from appointments.models import Appointment
from consultations.models import Consultation
from diagnosis.models import Condition, Symptom
from billing.models import TariffCode, TariffRate, Invoice, InvoiceItem
from medaid.models import SchemeConfig
from tasks.models import Task


class Command(BaseCommand):
    help = 'Set up demo users, patients, appointments, and medical-aid config'

    def handle(self, *args, **options):
        self.stdout.write('[*] Setting up demo data...\n')

        # ─────────────────────────────────────────────────────────────────
        # 1. USERS & GROUPS
        # ─────────────────────────────────────────────────────────────────
        doctor_group, _ = Group.objects.get_or_create(name='Doctor')
        reception_group, _ = Group.objects.get_or_create(name='Reception')

        # Doctor user
        doc_user, created = User.objects.get_or_create(
            username='doctor',
            defaults={
                'first_name': 'Tamuka',
                'last_name': 'Chivonivoni',
                'email': 'doctor@medicaregp.local',
                'is_staff': True,
            }
        )
        if created:
            doc_user.set_password('doctor123')
            doc_user.save()
        doc_user.groups.add(doctor_group)
        self.stdout.write('[OK] Doctor user: doctor / doctor123')

        # Receptionist user
        rec_user, created = User.objects.get_or_create(
            username='receptionist',
            defaults={
                'first_name': 'Sarah',
                'last_name': 'Motlanthe',
                'email': 'reception@medicaregp.local',
                'is_staff': True,
            }
        )
        if created:
            rec_user.set_password('reception123')
            rec_user.save()
        rec_user.groups.add(reception_group)
        self.stdout.write('[OK] Receptionist user: receptionist / reception123\n')

        # ─────────────────────────────────────────────────────────────────
        # 2. MEDICAL-AID PLAN CONFIGS
        # ─────────────────────────────────────────────────────────────────
        MedicalAidPlanConfig.objects.get_or_create(
            scheme_name='Momentum Health',
            plan_name='Essential',
            defaults={
                'visits_per_year': 6,
                'warn_at': 5,
            }
        )
        MedicalAidPlanConfig.objects.get_or_create(
            scheme_name='Discovery Health',
            plan_name='Core',
            defaults={
                'visits_per_year': 12,
                'warn_at': 10,
            }
        )
        MedicalAidPlanConfig.objects.get_or_create(
            scheme_name='Bonitas',
            plan_name='Classic',
            defaults={
                'visits_per_year': 8,
                'warn_at': 7,
            }
        )
        self.stdout.write('[OK] Medical-aid plan configs created\n')

        # ─────────────────────────────────────────────────────────────────
        # 3. MEDICAL-AID SCHEME CONFIGS
        # ─────────────────────────────────────────────────────────────────
        SchemeConfig.objects.get_or_create(
            scheme_name='Momentum Health',
            defaults={'adapter': 'manual'}
        )
        SchemeConfig.objects.get_or_create(
            scheme_name='Discovery Health',
            defaults={'adapter': 'manual'}
        )
        SchemeConfig.objects.get_or_create(
            scheme_name='Bonitas',
            defaults={'adapter': 'manual'}
        )
        self.stdout.write('[OK] Scheme configs created\n')

        # ─────────────────────────────────────────────────────────────────
        # 4. SAMPLE PATIENTS
        # ─────────────────────────────────────────────────────────────────
        patients_data = [
            {
                'first_name': 'Thabo',
                'last_name': 'Mokoena',
                'date_of_birth': date(1980, 5, 10),
                'id_number': '8005105800085',
                'gender': 'M',
                'phone': '0821234567',
                'email': 'thabo@example.com',
                'chronic_conditions': 'Hypertension',
                'smoking_status': 'Current',
                'allergies': 'Penicillin',
                'medical_aid_name': 'Momentum Health',
                'medical_aid_plan': 'Essential',
                'medical_aid_number': 'MOM123456789',
            },
            {
                'first_name': 'Naledi',
                'last_name': 'Dlamini',
                'date_of_birth': date(1975, 8, 22),
                'id_number': '7508225801123',
                'gender': 'F',
                'phone': '0827654321',
                'email': 'naledi@example.com',
                'chronic_conditions': 'Type 2 Diabetes',
                'smoking_status': 'Never',
                'allergies': '',
                'medical_aid_name': 'Discovery Health',
                'medical_aid_plan': 'Core',
                'medical_aid_number': 'DIS987654321',
            },
            {
                'first_name': 'Sipho',
                'last_name': 'Banda',
                'date_of_birth': date(1990, 1, 15),
                'id_number': '9001155801234',
                'gender': 'M',
                'phone': '0829876543',
                'email': 'sipho@example.com',
                'chronic_conditions': '',
                'smoking_status': 'Former',
                'allergies': 'Sulfonamides',
                'medical_aid_name': 'Bonitas',
                'medical_aid_plan': 'Classic',
                'medical_aid_number': 'BON456789123',
            },
        ]

        patients = {}
        for p_data in patients_data:
            patient, created = Patient.objects.get_or_create(
                id_number=p_data['id_number'],
                defaults=p_data
            )
            patients[p_data['first_name']] = patient
            if created:
                self.stdout.write(f'  [OK] {patient.first_name} {patient.last_name}')

        self.stdout.write('[OK] Sample patients created\n')

        # ─────────────────────────────────────────────────────────────────
        # 5. SAMPLE APPOINTMENTS
        # ─────────────────────────────────────────────────────────────────
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)

        appointment_data = [
            {
                'patient': patients['Thabo'],
                'date': today,
                'time': '10:00',
                'status': 'Scheduled',
                'reason': 'Consultation - Hypertension review',
            },
            {
                'patient': patients['Naledi'],
                'date': today,
                'time': '10:30',
                'status': 'Scheduled',
                'reason': 'Consultation - Blood sugar check',
            },
            {
                'patient': patients['Sipho'],
                'date': tomorrow,
                'time': '14:00',
                'status': 'Scheduled',
                'reason': 'Online Consultation (Video call) - general checkup',
            },
            {
                'patient': patients['Thabo'],
                'date': next_week,
                'time': '11:00',
                'status': 'Scheduled',
                'reason': 'Follow-up on medication',
            },
        ]

        for appt_data in appointment_data:
            appt, created = Appointment.objects.get_or_create(
                patient=appt_data['patient'],
                date=appt_data['date'],
                time=appt_data['time'],
                defaults={
                    'status': appt_data['status'],
                    'reason': appt_data['reason'],
                }
            )
            if created:
                self.stdout.write(
                    f'  [OK] {appt.patient.first_name} - {appt.reason} '
                    f'({appt.date} {appt.time})'
                )

        self.stdout.write('[OK] Sample appointments created\n')

        # ─────────────────────────────────────────────────────────────────
        # 6. SAMPLE CONSULTATION
        # ─────────────────────────────────────────────────────────────────
        thabo_appt = Appointment.objects.filter(patient=patients['Thabo']).first()
        if thabo_appt:
            consult, created = Consultation.objects.get_or_create(
                patient=patients['Thabo'],
                appointment=thabo_appt,
                defaults={
                    'date': today,
                    'chief_complaint': 'Routine hypertension review',
                    'subjective': 'Patient reports feeling well. No new symptoms.',
                    'objective': 'BP: 140/90, HR: 78, temp: 36.8°C',
                    'assessment': 'Well-controlled hypertension',
                    'plan': 'Continue current medication. Recheck in 3 months.',
                }
            )
            if created:
                self.stdout.write(f'  [OK] Consultation created for {patients["Thabo"].first_name}\n')

        # ─────────────────────────────────────────────────────────────────
        # 7. SAMPLE TASKS
        # ─────────────────────────────────────────────────────────────────
        task_data = [
            {
                'patient': patients['Thabo'],
                'title': 'Book annual blood work',
                'due_date': today + timedelta(days=7),
                'priority': 'Medium',
                'done': False,
            },
            {
                'patient': patients['Naledi'],
                'title': 'Send HbA1c results to patient',
                'due_date': today,
                'priority': 'High',
                'done': False,
            },
        ]

        for task_data_item in task_data:
            task, created = Task.objects.get_or_create(
                patient=task_data_item['patient'],
                title=task_data_item['title'],
                defaults={
                    'due_date': task_data_item['due_date'],
                    'priority': task_data_item['priority'],
                    'done': task_data_item['done'],
                }
            )
            if created:
                self.stdout.write(f'  [OK] Task: {task.title}')

        self.stdout.write('[OK] Sample tasks created\n')

        # ─────────────────────────────────────────────────────────────────
        # 8. TARIFF SETUP (for billing)
        # ─────────────────────────────────────────────────────────────────
        # Create sample tariff codes for billing
        consultation_tariff, _ = TariffCode.objects.get_or_create(
            code='CONS',
            defaults={
                'description': 'Consultation',
                'category': 'Medical',
            }
        )
        # Ensure there's a rate
        TariffRate.objects.get_or_create(
            tariff=consultation_tariff,
            effective_from=date(2026, 1, 1),
            defaults={'amount': Decimal('350.00')}
        )
        self.stdout.write('[OK] Tariff codes created\n')

        # ─────────────────────────────────────────────────────────────────
        # SUMMARY
        # ─────────────────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            '\n[SUCCESS] Demo setup complete!\n'
            '\nLogin credentials:\n'
            '  Doctor: doctor / doctor123\n'
            '  Receptionist: receptionist / reception123\n'
            '\nSample patients created with appointments and tasks.\n'
            'Visit http://localhost:8000/app/ to start.\n'
        ))
