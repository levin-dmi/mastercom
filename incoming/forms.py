from django.forms import ModelForm, Form, ChoiceField, Select
from .models import *


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ('key', 'name', 'description', )


class ContractForm(ModelForm):
    class Meta:
        model = Contract
        fields = ('number', 'date', 'name', 'description', 'project', 'total_sum', 'material_sum', 'work_sum',
                  'prepaid', 'prepaid_close_method', 'retention_percent', 'status')


class ActForm(ModelForm):
    class Meta:
        model = Act
        fields = ('number', 'date', 'contract', 'total_sum', 'material_sum', 'work_sum', 'status')


class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ('number', 'date', 'contract', 'total_sum', 'prepaid_sum', 'retention_sum', 'status')

class ListFilterForm(Form):
    projects = [['', 'ВСЕ'],] + [[str(obj.pk), obj] for obj in Project.objects.all()]
    project = ChoiceField(widget=Select(), choices=projects, required=False)
    contracts = [['', 'ВСЕ'], ] + [[str(obj.pk), obj] for obj in Contract.objects.all()]
    contract = ChoiceField(widget=Select(), choices=contracts, required=False)

