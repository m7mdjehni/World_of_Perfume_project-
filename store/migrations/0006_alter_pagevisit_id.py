from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_pagevisit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pagevisit',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]