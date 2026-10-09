from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_alter_perfume_image_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageVisit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('visited_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-visited_at'],
            },
        ),
    ]
