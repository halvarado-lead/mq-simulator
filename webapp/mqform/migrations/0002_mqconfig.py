from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mqform', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MqConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('queue_manager', models.CharField(default='AUTORIZA', max_length=128)),
                ('channel', models.CharField(default='SYSTEM.ADMIN.SVRCONN', max_length=128)),
                ('host', models.CharField(default='ibmmq', max_length=128)),
                ('port', models.CharField(default='1414', max_length=10)),
                ('queue_name', models.CharField(default='BOFTD_ENV', max_length=128)),
                ('user', models.CharField(default='admin', max_length=128)),
                ('password', models.CharField(default='admin123', max_length=256)),
            ],
        ),
    ]
