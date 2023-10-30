import django_filters
from incoming.models import *

def get_contract_choices(request):
    if request is None:
        return Contract.objects.all()

    if request.GET.get('contract__project', '') != '':
        contracts = Contract.objects.filter(project=request.GET['contract__project'])
    else:
        contracts = Contract.objects.all()

    if 'inc/' in request.path:
        return contracts.filter(contract_type=Contract.ContractType.SALE)
    else:
        return contracts.filter(contract_type=Contract.ContractType.BUY)


def get_project_choices(request):
    if request is None:
        return Project.objects.all()

    if request.GET.get('contract', '') != '':
        contract = Contract.objects.get(id=request.GET['contract'])
        projects = Project.objects.filter(id=contract.project.pk)
    else:
        projects = Project.objects.all()

    return projects


class ActFilter(django_filters.FilterSet):
    contract__project = django_filters.ModelChoiceFilter(field_name = "contract__project",
                                               label = "Проект",
                                               queryset = get_project_choices)
    contract = django_filters.ModelChoiceFilter(field_name = "contract",
                                               label = "Договор",
                                               queryset = get_contract_choices)

    class Meta:
        model = Act
        fields = ['contract__project', 'contract',]


class PaymentFilter(ActFilter):
    class Meta:
        model = Payment
        fields = ['contract__project', 'contract', ]


class ContractFilter(django_filters.FilterSet):
    project = django_filters.ModelChoiceFilter(field_name = "project",
                                               label = "Проект",
                                               queryset = Project.objects.all())

    class Meta:
        model = Contract
        fields = ['project']