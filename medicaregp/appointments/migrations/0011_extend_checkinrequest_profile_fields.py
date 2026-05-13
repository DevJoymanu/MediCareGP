from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0010_checkinrequest_alcohol_use_checkinrequest_alt_phone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='checkinrequest',
            name='home_language',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='marital_status',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='residential_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='postal_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='responsible_surname',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='responsible_first_name',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='responsible_title',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='responsible_id_number',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='responsible_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='responsible_tel_h',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='responsible_tel_w',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='responsible_cell',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='work_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='work_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='principal_member_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='principal_member_id',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='dependant_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='previous_surgeries',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='family_history',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='substance_use',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='next_of_kin_address',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='next_of_kin_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='referred_by_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='referred_by_phone',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='referred_by_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='checkinrequest',
            name='consent_to_treat',
            field=models.BooleanField(default=False),
        ),
    ]
