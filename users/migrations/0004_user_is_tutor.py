from django.db import migrations, models


def set_is_tutor_for_existing_curators(apps, schema_editor):
    User = apps.get_model('users', 'User')
    Group = apps.get_model('students', 'Group')
    curator_ids = Group.objects.values_list('curators', flat=True).distinct()
    User.objects.filter(pk__in=curator_ids).update(is_tutor=True)


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_group_curators_m2m'),
        ('users', '0003_user_send_emails'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_tutor',
            field=models.BooleanField(
                default=False,
                help_text='Определяет, может ли пользователь быть назначен куратором группы',
                verbose_name='Куратор',
            ),
        ),
        migrations.RunPython(
            set_is_tutor_for_existing_curators,
            migrations.RunPython.noop,
        ),
    ]
