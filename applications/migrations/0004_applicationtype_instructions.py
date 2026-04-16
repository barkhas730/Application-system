# Generated manually — ApplicationType.instructions нэмэгдлээ
# (model.py-д байсан боловч migration-д ороогүй байсан)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # 0003 target_department нэмсэн байна
        ('applications', '0003_applicationtype_target_department'),
    ]

    operations = [
        # instructions талбар нэмэх
        migrations.AddField(
            model_name='applicationtype',
            name='instructions',
            field=models.TextField(blank=True, default='', verbose_name='Заавар / Анхааруулга'),
            preserve_default=False,
        ),
    ]
