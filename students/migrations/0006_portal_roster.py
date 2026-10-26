from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('students', '0005_group_curators_m2m')]
    operations = [
        migrations.AddField(model_name='group', name='portal_id', field=models.CharField(max_length=32, unique=True, null=True, blank=True, editable=False)),
        migrations.AddField(model_name='student', name='portal_id', field=models.CharField(max_length=32, unique=True, null=True, blank=True, editable=False)),
        migrations.AddField(model_name='student', name='email', field=models.EmailField(max_length=254, blank=True, verbose_name='Почта')),
    ]
