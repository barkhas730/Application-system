# Generated manually — ApplicationType.target_department нэмэгдлээ

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0002_application_assigned_to_alter_application_priority'),
    ]

    operations = [
        # Хариуцах хэлтэс талбар нэмэх — хоосон утгатай (бүх захирлууд)
        migrations.AddField(
            model_name='applicationtype',
            name='target_department',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                verbose_name='Хариуцах хэлтэс',
            ),
        ),
    ]
