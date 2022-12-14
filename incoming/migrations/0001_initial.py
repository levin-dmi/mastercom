# Generated by Django 3.2.16 on 2022-11-29 10:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ActStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='Название')),
            ],
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(blank=True, db_index=True, max_length=16, null=True, verbose_name='Номер')),
                ('date', models.DateField(blank=True, null=True, verbose_name='Дата')),
                ('name', models.CharField(blank=True, max_length=32, null=True, verbose_name='Название')),
                ('description', models.CharField(blank=True, max_length=256, null=True, verbose_name='Описание')),
                ('total_sum', models.IntegerField(blank=True, null=True, verbose_name='Сумма')),
                ('material_sum', models.IntegerField(blank=True, null=True, verbose_name='Материалы')),
                ('work_sum', models.IntegerField(blank=True, null=True, verbose_name='Работы')),
                ('prepaid', models.IntegerField(blank=True, null=True, verbose_name='Аванс')),
                ('retention_percent', models.FloatField(blank=True, null=True, verbose_name='Процент удержания с КС')),
            ],
        ),
        migrations.CreateModel(
            name='ContractStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='Название')),
            ],
        ),
        migrations.CreateModel(
            name='PaymentStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='Название')),
            ],
        ),
        migrations.CreateModel(
            name='PrepaidCloseMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.IntegerField(verbose_name='Код для алгоритма')),
                ('name', models.CharField(blank=True, max_length=32, null=True, verbose_name='Название')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=32, verbose_name='Код')),
                ('name', models.CharField(blank=True, max_length=32, null=True, verbose_name='Название')),
                ('description', models.CharField(blank=True, max_length=256, null=True, verbose_name='Описание')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(blank=True, db_index=True, max_length=16, null=True, verbose_name='Номер')),
                ('date', models.DateField(blank=True, null=True, verbose_name='Дата')),
                ('total_sum', models.IntegerField(blank=True, null=True, verbose_name='Сумма')),
                ('prepaid_sum', models.IntegerField(blank=True, null=True, verbose_name='Сумма аванса')),
                ('contract', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='incoming.contract', verbose_name='Договор')),
                ('status', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='incoming.paymentstatus', verbose_name='Статус')),
            ],
        ),
        migrations.AddField(
            model_name='contract',
            name='prepaid_close_method',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='incoming.prepaidclosemethod', verbose_name='Удержание аванса'),
        ),
        migrations.AddField(
            model_name='contract',
            name='project',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='incoming.project', verbose_name='Проект'),
        ),
        migrations.AddField(
            model_name='contract',
            name='status',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='incoming.contractstatus', verbose_name='Статус'),
        ),
        migrations.CreateModel(
            name='Act',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(blank=True, db_index=True, max_length=16, null=True, verbose_name='Номер')),
                ('date', models.DateField(blank=True, null=True, verbose_name='Дата')),
                ('total_sum', models.IntegerField(blank=True, null=True, verbose_name='Сумма')),
                ('material_sum', models.IntegerField(blank=True, null=True, verbose_name='Материалы')),
                ('work_sum', models.IntegerField(blank=True, null=True, verbose_name='Работы')),
                ('contract', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='incoming.contract', verbose_name='Договор')),
                ('status', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='incoming.actstatus', verbose_name='Статус')),
            ],
        ),
    ]
