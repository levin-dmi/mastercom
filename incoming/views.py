from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, FloatField
from .models import *
from .forms import *
from .services.calculations import *
from incoming.utils.mixins import LogCreateMixin, LogUpdateMixin, LogDeleteMixin, UserGroupTestMixin
from django.http import HttpResponse, HttpResponseRedirect
from .utils.filters import ActFilter, PaymentFilter, ContractFilter
from django_filters.views import FilterView
from django.contrib.auth.mixins import UserPassesTestMixin


class AnalyticView(UserGroupTestMixin, TemplateView):
    user_groups = ['Доходы']
    template_name = 'analytic.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'header': 'Аналитика'}
        objs = ContractAnalyticService().calc_contract_list_data()
        context['objs'] = objs
        return context


class ProjectsView(UserGroupTestMixin, ListView):
    user_groups = ['Доходы']
    model = Project
    template_name = 'list_view2.html'
    context_object_name = 'objs'
    extra_context = {'env':
                        {'header': 'Проекты',
                         'create_url': 'project_add',
                         'update_url': 'project_update',
                         'delete_url': 'project_delete',
                         'table_headers': ['Код проекта', 'Наименование'],
                         'columns': [{'name': 'key', 'url': 'project_view'},
                                     {'name': 'name'}],
                      }}


class ProjectDetailView(UserGroupTestMixin, DetailView):
    user_groups = ['Доходы']
    model = Project
    template_name = 'projects/project_view.html'


class ProjectCreateView(UserGroupTestMixin, CreateView):
    user_groups = ['Доходы']
    template_name = 'projects/project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')
    extra_content = {'env':{'header': 'Новый проект'}}


class ProjectUpdateView(UserGroupTestMixin, UpdateView):
    user_groups = ['Доходы']
    model = Project
    template_name = 'projects/project_update.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')


class ProjectDeleteView(UserGroupTestMixin, DeleteView):
    user_groups = ['Доходы']
    model = Project
    template_name = 'projects/project_delete.html'
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['undeleted_contracts'] = Contract.objects.filter(project=context['object'])
        return context


class ContractsView(UserGroupTestMixin, FilterView):
    user_groups = ['Доходы']
    template_name = 'list_view2.html'
    context_object_name = 'objs'
    filterset_class = ContractFilter
    extra_context = {'env': {'header': 'Договоры',
                             'create_url': 'contract_add',
                             'update_url': 'contract_update',
                             'delete_url': 'contract_delete',
                             'table_headers': ['Номер', 'Дата', 'Название', 'Проект', 'Сумма', 'Статус',],
                             'columns': [{'name': 'number', 'url': 'contract_view'},
                                      {'name': 'date'},
                                      {'name': 'name'},
                                      {'name': 'project'},
                                      {'name': 'total_sum', 'currency': True},
                                      {'name': 'status'},
                                      ],
                             }}
    queryset = Contract.objects.filter(contract_type=Contract.ContractType.SALE)


class ContractDetailView(UserGroupTestMixin, DetailView):
    user_groups = ['Доходы']
    model = Contract
    template_name = 'contracts/contract_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        header = f"Договор №{context['object'].number} от {context['object'].date}"
        context['env'] = {'header': header}
        calc = ContractAnalyticService().calculate(context['object'].pk)
        context.update(calc)
        return context


class ContractCreateView(UserGroupTestMixin, LogCreateMixin, CreateView):
    user_groups = ['Доходы']
    template_name = 'contracts/contract_create.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')
    log_data = ['number', 'date', 'total_sum', 'contract_type']
    initial = {'contract_type': Contract.ContractType.SALE}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'headr': 'Новый договор'}
        if 'project_id' in context['view'].kwargs:
            context['form'].initial['project'] = context['view'].kwargs['project_id']
        return context


class ContractUpdateView(UserGroupTestMixin, LogUpdateMixin, UpdateView):
    user_groups = ['Доходы']
    model = Contract
    template_name = 'contracts/contract_update.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')
    log_data = ['number', 'date', 'total_sum', 'contract_type'], ['total_sum']


class ContractDeleteView(UserGroupTestMixin, LogDeleteMixin, DeleteView):
    user_groups = ['Доходы']
    model = Contract
    template_name = 'contracts/contract_delete.html'
    success_url = reverse_lazy('contracts')
    log_data = ['number', 'date', 'total_sum', 'contract_type']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        undeleted_acts = Act.objects.filter(contract=context['object'])
        undeleted_payments = Payment.objects.filter(contract=context['object'])
        context['undeleted_acts'] = undeleted_acts
        context['undeleted_payments'] = undeleted_payments
        return context


class ActsView(UserGroupTestMixin, FilterView):
    user_groups = ['Доходы']
    template_name = 'list_view2.html'
    context_object_name = 'objs'
    filterset_class = ActFilter
    queryset = Act.objects.filter(contract__contract_type=Contract.ContractType.SALE)
    extra_context = {'env': {'header': 'Акты',
                             'create_url': 'act_add',
                             'update_url': 'act_update',
                             'delete_url': 'act_delete',
                             'table_headers': ['Номер', 'Дата', 'Договор', 'Сумма', 'Статус'],
                             'columns': [{'name': 'number', 'url': 'act_view'},
                                         {'name': 'date'},
                                         {'name': 'contract'},
                                         {'name': 'total_sum', 'currency': True},
                                         {'name': 'status'},],
                          }}


class ActDetailView(UserGroupTestMixin, DetailView):
    user_groups = ['Доходы']
    model = Act
    template_name = 'acts/act_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['calc'] = ContractAnalyticService().calc_act(context['object'].pk)
        return context


class ActCreateView(UserGroupTestMixin, LogCreateMixin, CreateView):
    user_groups = ['Доходы']
    template_name = 'acts/act_create.html'
    form_class = ActForm
    # success_url = reverse_lazy('acts')
    log_data = ['number', 'date', 'total_sum', 'contract__contract_type']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'contract_id' in context['view'].kwargs:
            context['form'].initial['contract'] = context['view'].kwargs['contract_id']

        return context

    def get_success_url(self):
        act_id = self.object.id
        return reverse_lazy('act_view', kwargs={'pk': act_id})


class ActUpdateView(UserGroupTestMixin, LogUpdateMixin, UpdateView):
    user_groups = ['Доходы']
    model = Act
    template_name = 'acts/act_update.html'
    form_class = ActForm
    success_url = reverse_lazy('acts')
    log_data = ['number', 'date', 'total_sum', 'contract__contract_type'], ['total_sum']


class ActDeleteView(UserGroupTestMixin, LogDeleteMixin, DeleteView):
    user_groups = ['Доходы']
    model = Act
    template_name = 'acts/act_delete.html'
    success_url = reverse_lazy('acts')
    log_data = ['number', 'date', 'total_sum', 'contract__contract_type']


class PaymentsView(UserGroupTestMixin, FilterView):
    user_groups = ['Доходы']
    template_name = 'list_view2.html'
    context_object_name = 'objs'
    filterset_class = PaymentFilter
    queryset = Payment.objects.filter(contract__contract_type=Contract.ContractType.SALE)
    extra_context = {'env': {'header': 'Оплаты',
                             'create_url': 'payment_add',
                             'update_url': 'payment_update',
                             'delete_url': 'payment_delete',
                             'table_headers': ['Номер платежа', 'Дата', 'Договор', 'Сумма', 'В т.ч. аванс', 'В т.ч. возврат удержаний'],
                             'columns': [{'name': 'number', 'url': 'payment_view'},
                                         {'name': 'date'},
                                         {'name': 'contract'},
                                         {'name': 'total_sum', 'currency': True},
                                         {'name': 'prepaid_sum', 'currency': True},
                                         {'name': 'retention_sum', 'currency': True},],
                          }}


class PaymentDetailView(UserGroupTestMixin, DetailView):
    user_groups = ['Доходы']
    model = Payment
    template_name = 'payments/payment_view.html'


class PaymentCreateView(UserGroupTestMixin, LogCreateMixin, CreateView):
    user_groups = ['Доходы']
    template_name = 'payments/payment_create.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')
    log_data = ['number', 'date', 'total_sum', 'contract__contract_type']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].initial['status'] = PaymentStatus.objects.get(key=PaymentStatusType.paid.value)
        if 'contract_id' in context['view'].kwargs:
            context['form'].initial['contract'] = context['view'].kwargs['contract_id']
        return context


class PaymentUpdateView(UserGroupTestMixin, LogUpdateMixin, UpdateView):
    user_groups = ['Доходы']
    model = Payment
    template_name = 'payments/payment_update.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')
    log_data = ['number', 'date', 'total_sum', 'contract__contract_type'], ['total_sum']


class PaymentDeleteView(UserGroupTestMixin, LogDeleteMixin, DeleteView):
    user_groups = ['Доходы']
    model = Payment
    template_name = 'payments/payment_delete.html'
    success_url = reverse_lazy('payments')
    log_data = ['number', 'date', 'total_sum', 'contract__contract_type']


class PartnersView(UserGroupTestMixin, ListView):
    user_groups = ['Подрядчики']
    model = Partner
    template_name = 'list_view2.html'
    context_object_name = 'objs'
    extra_context = {'env': {'header': 'Партнеры',
                             'create_url': 'partner_add',
                             'update_url': 'partner_update',
                             'delete_url': 'partner_delete',
                             'table_headers': ['ИНН', 'Наименование'],
                             'columns': [{'name': 'inn', 'url': 'partner_view'},
                                         {'name': 'name'}],
                          }}


class PartnerDetailView(UserGroupTestMixin, DetailView):
    user_groups = ['Подрядчики']
    model = Partner
    template_name = 'partners/partner_view.html'


class PartnerCreateView(UserGroupTestMixin, CreateView):
    user_groups = ['Подрядчики']
    template_name = 'create.html'
    form_class = PartnerForm
    success_url = reverse_lazy('partners')
    extra_context = {'env': {'header': 'Новый партнер',}}


class PartnerUpdateView(UserGroupTestMixin, UpdateView):
    user_groups = ['Подрядчики']
    model = Partner
    template_name = 'create.html'
    form_class = PartnerForm
    success_url = reverse_lazy('partners')
    extra_context = {'env': {'header': 'Обновить данные партнера', }}


class PartnerDeleteView(UserGroupTestMixin, DeleteView):
    user_groups = ['Подрядчики']
    model = Partner
    template_name = 'partners/partner_delete.html'
    success_url = reverse_lazy('partners')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'header': 'Удалить партнера'}
        context['undeleted_contracts'] = Contract.objects.filter(partner=context['object'])
        return context


class ContractsContractorView(ContractsView):
    user_groups = ['Подрядчики']
    queryset = Contract.objects.filter(contract_type=Contract.ContractType.BUY)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env']['columns'][0]['url'] = 'contract_contractor_view'
        context['env']['create_url'] = 'contract_contractor_add'
        context['env']['update_url'] = 'contract_contractor_update'
        context['env']['delete_url'] = 'contract_contractor_delete'
        return context


class ContractContractorDetailView(ContractDetailView):
    user_groups = ['Подрядчики']
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        header = f"Договор №{context['object'].number} от {context['object'].date}  [{context['object'].partner}]"
        context['env']['header'] = header
        return context
    pass


class ContractContractorCreateView(ContractCreateView):
    user_groups = ['Подрядчики']
    form_class = ContractForm
    success_url = reverse_lazy('contracts_contractor')
    initial = {'contract_type': Contract.ContractType.BUY}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'partner_id' in context['view'].kwargs:
            context['form'].initial['partner'] = context['view'].kwargs['partner_id']
        return context


class ContractContractorUpdateView(ContractUpdateView):
    user_groups = ['Подрядчики']
    success_url = reverse_lazy('contracts_contractor')


class ContractContractorDeleteView(ContractDeleteView):
    user_groups = ['Подрядчики']
    success_url = reverse_lazy('contracts_contractor')


class ActContractorView(ActsView):
    user_groups = ['Подрядчики']
    queryset = Act.objects.filter(contract__contract_type=Contract.ContractType.BUY)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env']['columns'][0]['url'] = 'act_contractor_view'
        context['env']['create_url'] = 'act_contractor_add'
        context['env']['update_url'] = 'act_contractor_update'
        context['env']['delete_url'] = 'act_contractor_delete'
        return context

class ActContractorDetailView(LoginRequiredMixin, DetailView):
    user_groups = ['Подрядчики']
    model = Act
    template_name = 'acts/act_view.html'


class ActContractorCreateView(ActCreateView):
    user_groups = ['Подрядчики']
    form_class = ActContractorForm

    def get_success_url(self):
        act_id = self.object.id
        return reverse_lazy('act_contractor_view', kwargs={'pk': act_id})


class ActContractorUpdateView(ActUpdateView):
    user_groups = ['Подрядчики']
    form_class = ActContractorForm
    success_url = reverse_lazy('acts_contractor')


class ActContractorDeleteView(ActDeleteView):
    user_groups = ['Подрядчики']
    success_url = reverse_lazy('acts_contractor')


class PaymentContractorView(PaymentsView):
    user_groups = ['Подрядчики']
    queryset = Payment.objects.filter(contract__contract_type=Contract.ContractType.BUY)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env']['columns'][0]['url'] = 'payment_contractor_view'
        context['env']['create_url'] = 'payment_contractor_add'
        context['env']['update_url'] = 'payment_contractor_update'
        context['env']['delete_url'] = 'payment_contractor_delete'
        return context


class PaymentContractorDetailView(PaymentDetailView):
    user_groups = ['Подрядчики']


class PaymentContractorCreateView(PaymentCreateView):
    user_groups = ['Подрядчики']
    form_class = PaymentContractorForm
    success_url = reverse_lazy('payments_contractor')


class PaymentContractorUpdateView(PaymentUpdateView):
    user_groups = ['Подрядчики']
    form_class = PaymentContractorForm
    success_url = reverse_lazy('payments_contractor')


class PaynmentContractorDeleteView(PaymentDeleteView):
    user_groups = ['Подрядчики']
    success_url = reverse_lazy('payments_contractor')


class AnalyticContractorView(AnalyticView):
    user_groups = ['Подрядчики']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'header': 'Аналитика по подрядчикам'}
        objs = ContractAnalyticService().calc_partner_list_data()
        context['objs'] = objs
        return context

# @login_required()
# def analytic_contractor(request):
#     objs = ContractAnalyticService().calc_contract_list_data()
#     env = {'header': 'Аналитика'}
#     context = {'objs': objs, 'env': env, }
#     return render(request, 'analytic.html', context)


def redirect_to_incoming(request):
    if request.user.groups.filter(name='Доходы').exists():
        response = redirect('/incoming/')
    elif request.user.groups.filter(name='Подрядчики').exists():
        response = redirect('/incoming/ctr/analytic_contractor/')
    else:
        response = redirect('/accounts/login/')
    return response


def act_sum_for_contract(contract_pk: int, field: str) -> float:
    act_sum = Act.objects.aggregate(sum=Sum(field,
                                            output_field=FloatField(),
                                            filter=Q(contract__pk=contract_pk)))['sum']
    return float(act_sum or 0)


def payment_sum_for_contract(contract_pk: int, field: str) -> float:
    act_sum = Payment.objects.aggregate(sum=Sum(field,
                                                output_field=FloatField(),
                                                filter=Q(contract__pk=contract_pk)))['sum']
    return float(act_sum or 0)
