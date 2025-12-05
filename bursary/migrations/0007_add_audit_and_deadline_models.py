# Generated migration for new models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bursary', '0006_bursaryapplication_bursary_bur_referen_59789d_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationDeadline',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Application Deadlines',
                'ordering': ['-end_date'],
            },
        ),
        migrations.CreateModel(
            name='ApplicationStatusLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(blank=True, max_length=20, null=True)),
                ('new_status', models.CharField(max_length=20)),
                ('reason', models.TextField(blank=True, null=True)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_logs', to='bursary.bursaryapplication')),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='application_status_changes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Application Status Logs',
                'ordering': ['-changed_at'],
            },
        ),
    ]
