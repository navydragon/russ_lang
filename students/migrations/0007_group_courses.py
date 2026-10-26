from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('students', '0006_portal_roster'), ('courses', '0002_course_websoft_id')]
    operations = [migrations.AddField(model_name='group', name='courses', field=models.ManyToManyField(to='courses.course', blank=True, related_name='groups', verbose_name='Курсы'))]
