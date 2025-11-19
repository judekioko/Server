from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bursary', '0009_make_id_number_nonunique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bursaryapplication',
            name='id_number',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]