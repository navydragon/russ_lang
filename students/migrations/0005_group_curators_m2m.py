from django.conf import settings
from django.db import migrations, models


def migrate_curator_to_curators(apps, schema_editor):
    Group = apps.get_model('students', 'Group')
    for group in Group.objects.exclude(curator_id__isnull=True):
        group.curators.add(group.curator_id)


def reverse_migrate_curators_to_curator(apps, schema_editor):
    Group = apps.get_model('students', 'Group')
    for group in Group.objects.all():
        curator = group.curators.first()
        if curator:
            group.curator_id = curator.pk
            group.save(update_fields=['curator_id'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('students', '0004_remove_student_sid'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='curators',
            field=models.ManyToManyField(
                blank=True,
                related_name='curated_groups',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Кураторы',
            ),
        ),
        migrations.RunPython(
            migrate_curator_to_curators,
            reverse_migrate_curators_to_curator,
        ),
        migrations.RemoveField(
            model_name='group',
            name='curator',
        ),
    ]
