from django.db import models


class Project(models.Model):
    key = models.CharField(max_length=32, db_index=True, verbose_name='Код')  # МК2203
    name = models.CharField(max_length=32, null=True, blank=True, verbose_name='Название')  # Клин
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    objects = models.Manager()

    def __str__(self):
        return f"[{self.key}] {self.name}"

    class Meta:
        verbose_name_plural = 'Проекты'
        verbose_name = 'Проект'
        ordering = ['name']


class Contract(models.Model):
    number = models.CharField(max_length=16, db_index=True, null=True, blank=True, verbose_name='Номер')
    date = models.DateField(null=True, blank=True, verbose_name='Дата')
    name = models.CharField(max_length=32, null=True, blank=True, verbose_name='Название')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    project = models.ForeignKey('Project', null=True, on_delete=models.PROTECT, verbose_name='Проект')
    total_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Сумма')
    material_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Материалы')
    work_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Работы')
    prepaid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Аванс')
    prepaid_close_method = models.ForeignKey('PrepaidCloseMethod', null=True, on_delete=models.PROTECT,
                                             verbose_name='Удержание аванса')
    retention_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                            verbose_name='Процент удержания с КС')
    status = models.ForeignKey('ContractStatus', null=True, on_delete=models.PROTECT, verbose_name='Статус')
    objects = models.Manager()

    def __str__(self):
        return f"№{self.number} от {self.date} ({self.name}), на сумму {num_with_spaces(self.total_sum)}р."

    class Meta:
        verbose_name_plural = 'Договоры'
        verbose_name = 'Договор'
        ordering = ['date']


class Act(models.Model):
    number = models.CharField(max_length=16, db_index=True, null=True, blank=True, verbose_name='Номер')
    date = models.DateField(null=True, blank=True, verbose_name='Дата')
    contract = models.ForeignKey('Contract', null=True, on_delete=models.PROTECT, verbose_name='Договор')
    status = models.ForeignKey('ActStatus', null=True, on_delete=models.PROTECT, verbose_name='Статус')
    total_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Сумма')
    material_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Материалы')
    work_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Работы')
    objects = models.Manager()

    def __str__(self):
        return f"№{self.number} от {self.date} на сумму {num_with_spaces(self.total_sum)}р., " \
               f"по договору {self.contract}"

    class Meta:
        verbose_name_plural = 'Акты'
        verbose_name = 'Акт'
        ordering = ['date']


class Payment(models.Model):
    number = models.CharField(max_length=16, db_index=True, null=True, blank=True, verbose_name='Номер')
    date = models.DateField(null=True, blank=True, verbose_name='Дата')
    contract = models.ForeignKey('Contract', null=True, on_delete=models.SET_NULL, verbose_name='Договор')
    status = models.ForeignKey('PaymentStatus', null=True, on_delete=models.PROTECT, verbose_name='Статус')
    total_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Сумма')
    prepaid_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                      verbose_name='Сумма аванса')
    objects = models.Manager()

    def __str__(self):
        return f"№{self.number} от {self.date} на сумму {num_with_spaces(self.total_sum)}р., " \
               f"по договору {self.contract}"

    class Meta:
        verbose_name_plural = 'Платежи'
        verbose_name = 'Платеж'
        ordering = ['date']


class PrepaidCloseMethod(models.Model):
    key = models.IntegerField(verbose_name='Код для алгоритма')
    name = models.CharField(max_length=32, null=True, blank=True, verbose_name='Название')
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Способы закрытия аванса'
        verbose_name = 'Способ закрытия аванса'
        ordering = ['key']


class ContractStatus(models.Model):
    key = models.IntegerField(verbose_name='Код для алгоритма')
    name = models.CharField(max_length=32, verbose_name='Название')
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Статусы договоров'
        verbose_name = 'Статус договора'
        ordering = ['key']


class ActStatus(models.Model):
    key = models.IntegerField(verbose_name='Код для алгоритма')
    name = models.CharField(max_length=32, verbose_name='Название')
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Статусы актов'
        verbose_name = 'Статус акта'
        ordering = ['key']


class PaymentStatus(models.Model):
    key = models.IntegerField(verbose_name='Код для алгоритма')
    name = models.CharField(max_length=32, verbose_name='Название')
    objects = models.Manager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Статусы платежей'
        verbose_name = 'Статус платежа'
        ordering = ['key']


def num_with_spaces(num) -> str:
    """Возвращает число в виде строки с разрядами, разделенными пробелом и запятой, разделяющей дробную часть"""
    return f"{num:,}".replace(',', ' ').replace('.', ',')


def int_num_with_spaces(num) -> str:
    """Возвращает число в виде строки с разрядами, разделенными пробелом и без дробной части"""
    if num:
        return f"{round(num):,}".replace(',', ' ').replace('.', ',')
    else:
        return '0'
