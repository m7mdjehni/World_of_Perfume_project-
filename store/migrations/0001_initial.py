from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Perfume',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, default='No description', max_length=500)),
                ('price', models.CharField(blank=True, default='N/A', max_length=50)),
                ('image', models.CharField(blank=True, default='img/perfume1.jpg', help_text='Path (relative to static/store/) or full URL to the product image.', max_length=500)),
                ('show_in_carousel', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
