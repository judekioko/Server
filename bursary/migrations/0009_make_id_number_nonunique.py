from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bursary', '0008_bursaryapplication_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bursaryapplication',
            name='id_number',
            field=models.CharField(max_length=50),
        ),
    ]