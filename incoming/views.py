from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormMixin
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, FloatField
from .models import *
from .forms import *
from .services.calculations import *
from incoming.utils.mixins import LogCreateMixin, LogUpdateMixin, LogDeleteMixin
from django.http import HttpResponse, HttpResponseRedirect
from .utils.filters import ActFilter, PaymentFilter, ContractFilter
from django_filters.views import FilterView


@login_required()
def index(request):
    objs = {}
    for ctr in Contract.objects.filter(contract_type=Contract.ContractType.SALE):
        if ctr.project.key not in objs:
            objs[ctr.project.key] = {'name': ctr.project, 'pk': ctr.project.pk, 'contracts': {}, 'sum': {}}

        act_sum = Act.objects.aggregate(
            sum=Sum('total_sum',filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0
        pay_sum = Payment.objects.aggregate(
            sum=Sum('total_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0
        prepaid_pay_sum = Payment.objects.aggregate(
            sum=Sum('prepaid_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0
        retention_pay_sum = Payment.objects.aggregate(
            sum=Sum('retention_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0


        if ctr.can_calculated():
            debt_act_sum = (calc_paid_from_acts_d(ctr.total_sum,
                                               ctr.prepaid,
                                               PrepaidType(ctr.prepaid_close_method.key if ctr.prepaid_close_method else -1),
                                               ctr.retention_percent,
                                               act_sum)
                            - (pay_sum - prepaid_pay_sum - retention_pay_sum))
            debt_prepaid_sum = ctr.prepaid - prepaid_pay_sum
            retention = (act_sum * ctr.retention_percent / 100 - retention_pay_sum).quantize(DEC1)
            objs[ctr.project.key]['sum']['debt_act_sum'] = (
                    objs[ctr.project.key]['sum'].get('debt_act_sum', 0) + debt_act_sum)
            objs[ctr.project.key]['sum']['debt_prepaid_sum'] = (
                    objs[ctr.project.key]['sum'].get('debt_prepaid_sum', 0) + debt_prepaid_sum)
            objs[ctr.project.key]['sum']['retention'] = (
                    objs[ctr.project.key]['sum'].get('retention', 0) + retention)
        else:
            debt_act_sum, debt_prepaid_sum, retention = '?' * 3

        objs[ctr.project.key]['contracts'][ctr.pk] = {'pk': ctr.pk,
                                                      'num_name': f"{ctr.number} ({ctr.name})",
                                                      'date': ctr.date,
                                                      'total_sum': ctr.total_sum,
                                                      'act_sum': act_sum,
                                                      'pay_sum': pay_sum,

                                                      'debt_act_sum': debt_act_sum,
                                                      'debt_prepaid_sum': debt_prepaid_sum,
                                                      'retention': retention,
                                                      }

        objs[ctr.project.key]['sum']['total_sum'] = (
                objs[ctr.project.key]['sum'].get('total_sum', 0) + (ctr.total_sum or 0))
        objs[ctr.project.key]['sum']['act_sum'] = objs[ctr.project.key]['sum'].get('act_sum', 0) + act_sum
        objs[ctr.project.key]['sum']['pay_sum'] = objs[ctr.project.key]['sum'].get('pay_sum', 0) + pay_sum


    env = {'header': 'Аналитика'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'analytic.html', context)


class ProjectsView(LoginRequiredMixin, ListView):
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


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_view.html'


class ProjectCreateView(LoginRequiredMixin, CreateView):
    template_name = 'projects/project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')
    extra_content = {'env':{'header': 'Новый проект'}}


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_update.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project_delete.html'
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['undeleted_contracts'] = Contract.objects.filter(project=context['object'])
        return context


class ContractsView(LoginRequiredMixin, FilterView):
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


class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'contracts/contract_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        header = f"Договор №{context['object'].number} от {context['object'].date}"
        context['env'] = {'header': header}
        calc = ContractAnalyticService().calculate(context['object'].pk)
        context.update(calc)
        return context


class ContractCreateView(LoginRequiredMixin, LogCreateMixin, CreateView):
    template_name = 'contracts/contract_create.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')
    log_data = ['number', 'date', 'total_sum']
    initial = {'contract_type': Contract.ContractType.SALE}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'headr': 'Новый договор'}
        if 'project_id' in context['view'].kwargs:
            context['form'].initial['project'] = context['view'].kwargs['project_id']
        return context


class ContractUpdateView(LoginRequiredMixin, LogUpdateMixin, UpdateView):
    model = Contract
    template_name = 'contracts/contract_update.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')
    log_data = ['number', 'date', 'total_sum'], ['total_sum']


class ContractDeleteView(LoginRequiredMixin, LogDeleteMixin, DeleteView):
    model = Contract
    template_name = 'contracts/contract_delete.html'
    success_url = reverse_lazy('contracts')
    log_data = ['number', 'date', 'total_sum']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        undeleted_acts = Act.objects.filter(contract=context['object'])
        undeleted_payments = Payment.objects.filter(contract=context['object'])
        context['undeleted_acts'] = undeleted_acts
        context['undeleted_payments'] = undeleted_payments
        return context


class ActsView(LoginRequiredMixin, FilterView):
    template_name = 'list_view2.html'
    context_object_name = 'objs'
    filterset_class = ActFilter
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


@login_required()
def act_view(request, act_id):
    act = Act.objects.get(pk=act_id)
    calc = {'can_calculate': False, 'no_prepaid': False}
    if act.contract.can_calculated():
        calc['can_calculate'] = True
        calc['sum'] = calc_paid_from_acts_d(act.contract.total_sum,
                                            act.contract.prepaid,
                                            PrepaidType(
                                                act.contract.prepaid_close_method.key if act.contract.prepaid_close_method else -1),
                                            act.contract.retention_percent,
                                            act.total_sum)
        calc['acts_sum'] = Act.objects.aggregate(
            sum=Sum('total_sum', filter=Q(contract__pk=act.contract.pk)))['sum'] or DEC0

        fact_prepaid = Payment.objects.aggregate(
            sum=Sum('prepaid_sum', filter=Q(contract__pk=act.contract.pk)))['sum'] or DEC0
        if fact_prepaid < act.contract.prepaid:
            calc['no_prepaid'] = True
            calc['sum_corr'] = calc_paid_from_acts_d(act.contract.total_sum,
                                                fact_prepaid,
                                                     PrepaidType(
                                                         act.contract.prepaid_close_method.key if act.contract.prepaid_close_method else -1),
                                                act.contract.retention_percent,
                                                act.total_sum)
            calc['fact_prepaid'] = fact_prepaid
    context = {'act': act, 'calc': calc}
    return render(request, 'acts/act_view.html', context)


class ActCreateView(LoginRequiredMixin, LogCreateMixin, CreateView):
    template_name = 'acts/act_create.html'
    form_class = ActForm
    success_url = reverse_lazy('acts')
    log_data = ['number', 'date', 'total_sum']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'contract_id' in context['view'].kwargs:
            context['form'].initial['contract'] = context['view'].kwargs['contract_id']

        return context

    def get_success_url(self):
        act_id = self.object.id
        return reverse_lazy('act_view', kwargs={'act_id': act_id})

class ActUpdateView(LoginRequiredMixin, LogUpdateMixin, UpdateView):
    model = Act
    template_name = 'acts/act_update.html'
    form_class = ActForm
    success_url = reverse_lazy('acts')
    log_data = ['number', 'date', 'total_sum'], ['total_sum']


class ActDeleteView(LoginRequiredMixin, LogDeleteMixin, DeleteView):
    model = Act
    template_name = 'acts/act_delete.html'
    success_url = reverse_lazy('acts')
    log_data = ['number', 'date', 'total_sum']


class PaymentsView(LoginRequiredMixin, FilterView):
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


class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/payment_view.html'


class PaymentCreateView(LoginRequiredMixin, LogCreateMixin, CreateView):
    template_name = 'payments/payment_create.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')
    log_data = ['number', 'date', 'total_sum']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].initial['status'] = PaymentStatus.objects.get(key=PaymentStatusType.paid.value)
        if 'contract_id' in context['view'].kwargs:
            context['form'].initial['contract'] = context['view'].kwargs['contract_id']
        return context


class PaymentUpdateView(LoginRequiredMixin, LogUpdateMixin, UpdateView):
    model = Payment
    template_name = 'payments/payment_update.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')
    log_data = ['number', 'date', 'total_sum'], ['total_sum']


class PaymentDeleteView(LoginRequiredMixin, LogDeleteMixin, DeleteView):
    model = Payment
    template_name = 'payments/payment_delete.html'
    success_url = reverse_lazy('payments')
    log_data = ['number', 'date', 'total_sum']



class PartnersView(LoginRequiredMixin, ListView):
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


class PartnerDetailView(LoginRequiredMixin, DetailView):
    model = Partner
    template_name = 'partners/partner_view.html'


class PartnerCreateView(LoginRequiredMixin, CreateView):
    template_name = 'create.html'
    form_class = PartnerForm
    success_url = reverse_lazy('partners')
    extra_context = {'env': {'header': 'Новый партнер',}}


class PartnerUpdateView(LoginRequiredMixin, UpdateView):
    model = Partner
    template_name = 'create.html'
    form_class = PartnerForm
    success_url = reverse_lazy('partners')
    extra_context = {'env': {'header': 'Обновить данные партнера', }}


class PartnerDeleteView(LoginRequiredMixin, DeleteView):
    model = Partner
    template_name = 'partners/partner_delete.html'
    success_url = reverse_lazy('partners')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'header': 'Удалить партнера'}
        context['undeleted_contracts'] = Contract.objects.filter(partner=context['object'])
        return context


class ContractsContractorView(ContractsView):
    queryset = Contract.objects.filter(contract_type=Contract.ContractType.BUY)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env']['columns'][0]['url'] = 'contract_contractor_view'
        context['env']['create_url'] = 'contract_contractor_add'
        context['env']['update_url'] = 'contract_contractor_update'
        context['env']['delete_url'] = 'contract_contractor_delete'
        return context


class ContractContractorDetailView(ContractDetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        header = f"Договор №{context['object'].number} от {context['object'].date}  [{context['object'].partner}]"
        context['env']['header'] = header
        return context
    pass


class ContractContractorCreateView(ContractCreateView):
    form_class = ContractForm
    success_url = reverse_lazy('contracts_contractor')
    initial = {'contract_type': Contract.ContractType.BUY}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'partner_id' in context['view'].kwargs:
            context['form'].initial['partner'] = context['view'].kwargs['partner_id']
        return context


class ContractContractorUpdateView(ContractUpdateView):
    success_url = reverse_lazy('contracts_contractor')


class ContractContractorDeleteView(ContractDeleteView):
    success_url = reverse_lazy('contracts_contractor')


class PaymentContractorView(PaymentsView):
    queryset = Payment.objects.filter(contract__contract_type=Contract.ContractType.BUY)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env']['columns'][0]['url'] = 'payment_contractor_view'
        context['env']['create_url'] = 'payment_contractor_add'
        context['env']['update_url'] = 'payment_contractor_update'
        context['env']['delete_url'] = 'payment_contractor_delete'
        return context

class PaymentContractorDetailView(PaymentDetailView):
    pass


class PaymentContractorCreateView(PaymentCreateView):
    form_class = PaymentContractorForm
    success_url = reverse_lazy('payments_contractor')


class PaymentContractorUpdateView(PaymentUpdateView):
    form_class = PaymentContractorForm
    success_url = reverse_lazy('payments_contractor')


class PaynmentContractorDeleteView(PaymentDeleteView):
    success_url = reverse_lazy('payments_contractor')


@login_required()
def analytic_contractor(request):
    objs = {}
    for ctr in Contract.objects.filter(contract_type=Contract.ContractType.BUY):
        if ctr.partner.inn not in objs:
            objs[ctr.partner.inn] = {'name': ctr.partner, 'pk': ctr.partner.pk, 'contracts': {}, 'sum': {}}

        act_sum = Act.objects.aggregate(
            sum=Sum('total_sum',filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0
        pay_sum = Payment.objects.aggregate(
            sum=Sum('total_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0
        prepaid_pay_sum = Payment.objects.aggregate(
            sum=Sum('prepaid_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0
        retention_pay_sum = Payment.objects.aggregate(
            sum=Sum('retention_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0


        if ctr.can_calculated():
            debt_act_sum = (calc_paid_from_acts_d(ctr.total_sum,
                                               ctr.prepaid,
                                               PrepaidType(ctr.prepaid_close_method.key if ctr.prepaid_close_method else -1),
                                               ctr.retention_percent,
                                               act_sum)
                            - (pay_sum - prepaid_pay_sum - retention_pay_sum))
            debt_prepaid_sum = ctr.prepaid - prepaid_pay_sum
            retention = (act_sum * ctr.retention_percent / 100 - retention_pay_sum).quantize(DEC1)
            objs[ctr.partner.inn]['sum']['debt_act_sum'] = (
                    objs[ctr.partner.inn]['sum'].get('debt_act_sum', 0) + debt_act_sum)
            objs[ctr.partner.inn]['sum']['debt_prepaid_sum'] = (
                    objs[ctr.partner.inn]['sum'].get('debt_prepaid_sum', 0) + debt_prepaid_sum)
            objs[ctr.partner.inn]['sum']['retention'] = (
                    objs[ctr.partner.inn]['sum'].get('retention', 0) + retention)
        else:
            debt_act_sum, debt_prepaid_sum, retention = '?' * 3

        objs[ctr.partner.inn]['contracts'][ctr.pk] = {'pk': ctr.pk,
                                                      'num_name': f"{ctr.number} ({ctr.name})",
                                                      'date': ctr.date,
                                                      'total_sum': ctr.total_sum,
                                                      'act_sum': act_sum,
                                                      'pay_sum': pay_sum,

                                                      'debt_act_sum': debt_act_sum,
                                                      'debt_prepaid_sum': debt_prepaid_sum,
                                                      'retention': retention,
                                                      }

        objs[ctr.partner.inn]['sum']['total_sum'] = (
                objs[ctr.partner.inn]['sum'].get('total_sum', 0) + (ctr.total_sum or 0))
        objs[ctr.partner.inn]['sum']['act_sum'] = objs[ctr.partner.inn]['sum'].get('act_sum', 0) + act_sum
        objs[ctr.partner.inn]['sum']['pay_sum'] = objs[ctr.partner.inn]['sum'].get('pay_sum', 0) + pay_sum


    env = {'header': 'Аналитика'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'analytic.html', context)


def redirect_to_incoming(request):
    response = redirect('/incoming/')
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
