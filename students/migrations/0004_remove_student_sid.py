from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_student_sid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='sid',
        ),
        migrations.AlterField(
            model_name='student',
            name='code',
            field=models.CharField(max_length=50, unique=True, verbose_name='Код студента'),
        ),
    ]
