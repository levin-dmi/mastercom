from django.db import models

# from incoming.middleware import get_current_user


class Partner(models.Model):
    """Контрагент"""
    inn = models.CharField(max_length=12, db_index=True, verbose_name='ИНН')
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='Название')
    objects = models.Manager()

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name_plural = 'Контрагенты'
        verbose_name = 'Контрагент'
        ordering = ['name']


class Project(models.Model):
    """Проект"""
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
    """Договор"""
    class ContractType(models.TextChoices):
        SALE = 'sale', 'Продажа'
        BUY = 'buy', 'Закупка'


    number = models.CharField(max_length=16, db_index=True, null=True, blank=True, verbose_name='Номер')
    date = models.DateField(null=True, blank=True, verbose_name='Дата')
    name = models.CharField(max_length=32, null=True, blank=True, verbose_name='Название')
    description = models.TextField(null=True, blank=True, verbose_name='Описание')
    status = models.ForeignKey('ContractStatus', null=True, on_delete=models.PROTECT, verbose_name='Статус')

    project = models.ForeignKey('Project', null=True, on_delete=models.PROTECT, verbose_name='Проект')
    partner = models.ForeignKey('Partner', null=True, on_delete=models.PROTECT, verbose_name='Контрагент')
    contract_type = models.CharField(
        choices=ContractType.choices, max_length=10, default=ContractType.SALE, verbose_name='Тип договора')

    total_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Сумма')
    material_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Материалы')
    work_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Работы')
    prepaid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Аванс')
    prepaid_close_method = models.ForeignKey('PrepaidCloseMethod', null=True, blank=True, on_delete=models.PROTECT,
                                             verbose_name='Удержание аванса')
    retention_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                            verbose_name='Процент удержания с КС')

    objects = models.Manager()

    def __str__(self):
        total_sum = num_with_spaces(self.total_sum) if self.total_sum else '???'
        return f"№{self.number} от {self.date} ({self.name}), на сумму {total_sum}р."

    class Meta:
        verbose_name_plural = 'Договоры'
        verbose_name = 'Договор'
        ordering = ['date']

    def can_calculated(self):
        prepaid_close_method_ok = True if (self.prepaid_close_method is not None) or (self.prepaid == 0) else False
        if (None in [self.total_sum, self.material_sum, self.work_sum, self.prepaid,
                    self.retention_percent]) or not prepaid_close_method_ok:
            return False
        return True

    # def save(self, *args, **kwargs):
    #     orig_obj = Contract.objects.get(pk=self.pk) if self.pk else None
    #     save_to_change_log(self, orig_obj,
    #                        {'Номер договора': self.number,
    #                         'Дата договора': self.date,
    #                         'Новая сумма': self.total_sum},
    #                        None if not orig_obj else {'Старая сумма': str(orig_obj.total_sum)})
    #     super(Contract, self).save(*args, **kwargs)
    #
    # def delete(self, *args, **kwargs):
    #     orig_obj = Contract.objects.get(pk=self.pk) if self.pk else None
    #     save_delete_to_change_log(orig_obj,
    #                               {'Номер договора': orig_obj.number,
    #                                'Дата договора': orig_obj.date,
    #                                'Сумма': self.total_sum})
    #     super(Contract, self).delete(*args, **kwargs)


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

    # def save(self, *args, **kwargs):
    #     orig_obj = Act.objects.get(pk=self.pk) if self.pk else None
    #     save_to_change_log(self, orig_obj,
    #                        {'Номер акта': self.number,
    #                         'Дата акта': self.date,
    #                         'Новая сумма': self.total_sum},
    #                        None if not orig_obj else {'Старая сумма': str(orig_obj.total_sum)})
    #     super(Act, self).save(*args, **kwargs)
    #
    # def delete(self, *args, **kwargs):
    #     orig_obj = Act.objects.get(pk=self.pk) if self.pk else None
    #     save_delete_to_change_log(orig_obj,
    #                               {'Номер акта': orig_obj.number,
    #                                'Дата акта': orig_obj.date,
    #                                'Сумма': self.total_sum})
    #     super(Act, self).delete(*args, **kwargs)


class Payment(models.Model):
    number = models.CharField(max_length=16, db_index=True, null=True, blank=True, verbose_name='Номер')
    date = models.DateField(null=True, blank=True, verbose_name='Дата')
    contract = models.ForeignKey('Contract', null=True, on_delete=models.SET_NULL, verbose_name='Договор')
    status = models.ForeignKey('PaymentStatus', null=True, on_delete=models.PROTECT, verbose_name='Статус')
    total_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Общая сумма')
    prepaid_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                      verbose_name='Сумма аванса')
    retention_sum = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                        verbose_name='Сумма удержаний')
    objects = models.Manager()

    def __str__(self):
        return f"№{self.number} от {self.date} на сумму {num_with_spaces(self.total_sum)}р., " \
               f"по договору {self.contract}"

    class Meta:
        verbose_name_plural = 'Платежи'
        verbose_name = 'Платеж'
        ordering = ['date']

    # def save(self, *args, **kwargs):
    #     orig_obj = Payment.objects.get(pk=self.pk) if self.pk else None
    #     save_to_change_log(self, orig_obj,
    #                        {'Номер платежа': self.number,
    #                         'Дата платежа': self.date,
    #                         'Новая сумма': self.total_sum},
    #                        None if not orig_obj else {'Старая сумма': str(orig_obj.total_sum)})
    #     super(Payment, self).save(*args, **kwargs)
    #
    # def delete(self, *args, **kwargs):
    #     orig_obj = Payment.objects.get(pk=self.pk) if self.pk else None
    #     save_delete_to_change_log(orig_obj,
    #                               {'Номер акта': orig_obj.number,
    #                                'Дата акта': orig_obj.date,
    #                                'Сумма': self.total_sum})
    #     super(Payment, self).delete(*args, **kwargs)


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


class ChangeLog(models.Model):
    class LogAction(models.TextChoices):
        CREATE = 'create', 'Новая запись'
        UPDATE = 'update', 'Изменение в записи'
        DELETE = 'delete', 'Удаление записи'

    # TYPE_ACTION_ON_MODEL = [[i.name, i.value] for i in LogAction]

    changed = models.DateTimeField(auto_now=True, verbose_name='Дата/время изменения')
    model = models.CharField(max_length=255, verbose_name='Таблица', null=True)
    user = models.CharField(max_length=255, verbose_name='Автор изменения', null=True)
    action_on_model = models.CharField(
      choices=LogAction.choices, max_length=50, verbose_name='Действие', null=True)
    data = models.JSONField(verbose_name='Изменяемые данные модели')
    sent = models.BooleanField(default=False, verbose_name='Отправлено')
    objects = models.Manager()

    def __str__(self):
        return f"{self.action_on_model} в [{self.model}] от {self.changed}, автор {self.user}"

    class Meta:
        verbose_name_plural = 'История изменений'
        verbose_name = 'Запись об изменении'
        ordering = ['changed']


def num_with_spaces(num) -> str:
    """Возвращает число в виде строки с разрядами, разделенными пробелом и запятой, разделяющей дробную часть"""
    return f"{num:,}".replace(',', ' ').replace('.', ',')


# def save_to_change_log(obj, orig_obj, new_data: dict, update_data: dict):
#     """ Записываем в модель ChangeLog информацию о создании объекта и изменении цены
#
#     Args:
#         obj: новый объект
#         orig_obj: старый объект
#         new_data: информация по новому объекту, словарь
#         update_data: информация по старому обхъекту, словарь
#
#     Returns:
#         нет
#     """
#     if not orig_obj:  # new object
#         current_user = get_current_user()
#         ChangeLog(model=obj._meta.verbose_name_plural, action_on_model= ChangeLog.LogAction.CREATE,
#                   user=f"{current_user.first_name} {current_user.last_name}",
#                   data={k: str(v) for k, v in new_data.items()}).save()
#     else:
#         if orig_obj.total_sum != obj.total_sum:
#             current_user = get_current_user()
#             ChangeLog(model=obj._meta.verbose_name_plural, action_on_model=ChangeLog.LogAction.UPDATE,
#                       user=f"{current_user.first_name} {current_user.last_name}",
#                       data={k: str(v) for k, v in {**update_data, **new_data}.items()}).save()
#
#
# def save_delete_to_change_log(orig_obj, data: dict):
#     """ Записываем в модель ChangeLog информацию об удалении объекта
#
#     Args:
#         orig_obj: удаляемый объект
#         data: данные для записи, словарь
#
#     Returns: нет
#     """
#     current_user = get_current_user()
#     ChangeLog(model=orig_obj._meta.verbose_name_plural, action_on_model=ChangeLog.LogAction.DELETE,
#               user=f"{current_user.first_name} {current_user.last_name}",
#               data={k: str(v) for k, v in data.items()}).save()
