from django.db import migrations, models
import courses.websoft


def bind_russian_course(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    matches = Course.objects.using(schema_editor.connection.alias).filter(name='Русский язык для иностранных студентов')
    if matches.count() > 1:
        raise RuntimeError('Несколько основных курсов русского языка: проверьте дубли перед миграцией.')
    matches.update(websoft_id='7221015156608859696')


class Migration(migrations.Migration):
    dependencies = [('courses', '0001_initial')]
    operations = [
        migrations.AddField(model_name='course', name='websoft_id', field=models.CharField(max_length=32, unique=True, null=True, blank=True, verbose_name='ID WebSoft', validators=[courses.websoft.validate_websoft_id])),
        migrations.RunPython(bind_russian_course, migrations.RunPython.noop),
    ]
