from django.forms import ModelForm, Form, ChoiceField, Select, ValidationError
import sys
from .models import *
from decimal import Decimal


def is_migration():
    # Проверка аргументов командной строки на наличие миграции
    return 'makemigrations' in sys.argv or 'migrate' in sys.argv


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ('key', 'name', 'description', )


class ContractForm(ModelForm):
    class Meta:
        model = Contract
        fields = ('number', 'date', 'name', 'description', 'project', 'total_sum', 'material_sum', 'work_sum',
                  'prepaid', 'prepaid_close_method', 'retention_percent', 'status')

    def clean_total_sum(self):
        total_sum = (self.cleaned_data['total_sum'] or 0)

        # Проверяем
        if (total_sum or 0) < Decimal(self.data['material_sum'] or 0) + Decimal(self.data['work_sum'] or 0):
            raise ValidationError('Общая сумма не может быть меньше сумм материалов и работ')

        return self.cleaned_data['total_sum']

    def clean_prepaid(self):
        prepaid_sum = (self.cleaned_data['prepaid'] or 0)

        # Проверяем
        if (prepaid_sum or 0) > Decimal(self.data['total_sum'] or 0):
            raise ValidationError('Сумма аванса не может быть больше общей суммы')

        return self.cleaned_data['prepaid']

class ActForm(ModelForm):
    class Meta:
        model = Act
        fields = ('number', 'date', 'contract', 'total_sum', 'material_sum', 'work_sum', 'status')

    def clean_total_sum(self):
        total_sum = (self.cleaned_data['total_sum'] or 0)

        # Проверяем
        if (total_sum or 0) < Decimal(self.data['material_sum'] or 0) + Decimal(self.data['work_sum'] or 0):
            raise ValidationError('Общая сумма не может быть меньше сумм материалов и работ')

        return self.cleaned_data['total_sum']

class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ('number', 'date', 'contract', 'total_sum', 'prepaid_sum', 'retention_sum', 'status')

    def clean_total_sum(self):
        total_sum = self.cleaned_data['total_sum']

        # Проверяем
        if (total_sum or 0) < Decimal(self.data['prepaid_sum'] or 0) + Decimal(self.data['retention_sum'] or 0):
            raise ValidationError('Общая сумма не может быть меньше сумм аванса и возврата удержаний')

        return total_sum

    def clean_prepaid_sum(self):
        return self.cleaned_data['prepaid_sum'] or 0

    def clean_retention_sum(self):
        return self.cleaned_data['retention_sum'] or 0


class ListFilterForm(Form):
    if not is_migration():
        projects = [['', 'ВСЕ'],] + [[str(obj.pk), obj] for obj in Project.objects.all()]
        project = ChoiceField(widget=Select(), choices=projects, required=False)
        contracts = [['', 'ВСЕ'], ] + [[str(obj.pk), obj] for obj in Contract.objects.all()]
        contract = ChoiceField(widget=Select(), choices=contracts, required=False)
