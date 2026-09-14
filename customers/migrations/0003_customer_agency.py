from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agencies', '0001_initial'),
        ('customers', '0002_alter_customer_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='agency',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='customers',
                to='agencies.agency',
            ),
        ),
    ]