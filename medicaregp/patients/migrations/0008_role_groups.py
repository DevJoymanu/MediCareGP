# Data migration: create the RBAC groups (see medicaregp/roles.py).
from django.db import migrations

GROUPS = ['Doctor', 'Reception']


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in GROUPS:
        Group.objects.get_or_create(name=name)

    # Grandfather existing accounts into Doctor: before this migration every
    # login had full clinical access, so removing it silently would lock the
    # doctor out. New reception accounts get the Reception group explicitly.
    User = apps.get_model('auth', 'User')
    doctor = Group.objects.get(name='Doctor')
    for user in User.objects.all():
        user.groups.add(doctor)


def remove_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=GROUPS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0007_alter_patient_principal_member_id_and_more'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
