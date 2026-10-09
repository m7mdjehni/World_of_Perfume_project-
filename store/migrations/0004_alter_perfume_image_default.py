from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_cart_orders'),
    ]

    operations = [
        migrations.AlterField(
            model_name='perfume',
            name='image',
            field=models.CharField(
                blank=True,
                default='img/perfume1.png',
                help_text='Path (relative to static/store/) or full URL to the product image.',
                max_length=500,
            ),
        ),
    ]
