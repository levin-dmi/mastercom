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
from incoming.mixins import LogCreateMixin, LogUpdateMixin, LogDeleteMixin, AddCtxMixin
from django.http import HttpResponse, HttpResponseRedirect

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


class ProjectsView(LoginRequiredMixin, AddCtxMixin, ListView):
    model = Project
    template_name = 'list_view2.html'
    context_object_name = 'objs'
    context_vars = {'env':
                        {'header': 'Проекты',
                         'create_url': 'project_add',
                         'update_url': 'project_update',
                         'delete_url': 'project_delete',
                         'table_headers': ['Код проекта', 'Наименование'],
                         'columns': [{'name': 'key', 'url': 'project_view'},
                                     {'name': 'name'}],
                      }}



@login_required()
def project_view(request, project_id):
    prj = Project.objects.get(pk=project_id)
    context = {'prj': prj, }
    return render(request, 'projects/project_view.html', context)


class ProjectCreateView(LoginRequiredMixin, AddCtxMixin, CreateView):
    template_name = 'projects/project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')
    context_vars = {'env':{'header': 'Новый проект'}}


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


class ContractsView(LoginRequiredMixin, ListView):
    template_name = 'list_view2.html'
    context_object_name = 'objs'
    contract_type = Contract.ContractType.SALE

    def get_queryset(self):
        objs = Contract.objects.filter(contract_type=self.contract_type)
        form_initial = {}
        if self.request.GET:
            if self.request.GET['project']:
                objs = objs.filter(project=int(self.request.GET['project']))
                form_initial['project'] = self.request.GET['project']
            if self.request.GET['contract']:
                objs = objs.filter(pk=int(self.request.GET['contract']))
                form_initial['contract'] = self.request.GET['contract']
        return objs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['env'] = {'header': 'Договоры',
                          'create_url': 'contract_add',
                          'section': 'incoming',
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
                          }
        form = ListFilterForm()
        form_initial = {}
        if self.request.GET:
            if self.request.GET['project']:
                form_initial['project'] = self.request.GET['project']
            if self.request.GET['contract']:
                form_initial['contract'] = self.request.GET['contract']
        form.initial = form_initial
        context['form'] = form

        return context


class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'contracts/contract_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        header = f"Договор №{context['object'].number} от {context['object'].date}"
        if context['object'].partner:
            header += f" [{context['object'].partner}]"
        context['env'] = {'header': header}
        calc = ContractAnalyticService().calculate(context['object'].pk)
        context.update(calc)
        return context


class ContractCreateView(LoginRequiredMixin, LogCreateMixin, CreateView):
    template_name = 'contracts/contract_create.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')
    log_data = ['number', 'date', 'total_sum']

    def get_initial(self):
        initial = super().get_initial()
        initial['contract_type'] = Contract.ContractType.SALE
        return initial

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

@login_required()
def acts(request):
    objs = Act.objects.filter(contract__contract_type=Contract.ContractType.SALE)
    form_initial = {}
    if request.POST:
        if request.POST['project']:
            objs = objs.filter(contract__project=int(request.POST['project']))
            form_initial['project'] = request.POST['project']
        if request.POST['contract']:
            objs = objs.filter(contract=int(request.POST['contract']))
            form_initial['contract'] = request.POST['contract']
    form = ListFilterForm(initial=form_initial)
    env = {'header': 'Акты'}
    context = {'objs': objs, 'env': env, 'form': form}
    return render(request, 'list_view.html', context)


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


@login_required()
def payments(request):
    objs = Payment.objects.filter(contract__contract_type=Contract.ContractType.SALE)
    form_initial = {}
    if request.POST:
        if request.POST['project']:
            objs = objs.filter(contract__project=int(request.POST['project']))
            form_initial['project'] = request.POST['project']
        if request.POST['contract']:
            objs = objs.filter(contract=int(request.POST['contract']))
            form_initial['contract'] = request.POST['contract']
    form = ListFilterForm(initial=form_initial)
    env = {'header': 'Оплаты', }
    context = {'objs': objs, 'env': env, 'form': form, }
    return render(request, 'list_view.html', context)


@login_required()
def payment_view(request, payment_id):
    pay = Payment.objects.get(pk=payment_id)
    context = {'pay': pay, }
    return render(request, 'payments/payment_view.html', context)


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


class PartnerDetailView(LoginRequiredMixin, DetailView):
    model = Partner
    template_name = 'partners/partner_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'header': context['object']}
        return context


class PartnersView(LoginRequiredMixin, ListView):
    template_name = 'list_view2.html'
    context_object_name = 'objs'

    def get_queryset(self):
        return Partner.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'header': 'Партнеры',
                          'create_url': 'partner_add',
                          'update_url': 'partner_update',
                          'delete_url': 'partner_delete',
                          'table_headers': ['ИНН', 'Наименование'],
                          'columns': [{'name': 'inn', 'url': 'partner_view'},
                                      {'name': 'name'}],
                          }
        return context


class PartnerCreateView(LoginRequiredMixin, AddCtxMixin, CreateView):
    template_name = 'create.html'
    form_class = PartnerForm
    success_url = reverse_lazy('partners')
    context_vars = {'env': {'header': 'Новый партнер',}}


class PartnerUpdateView(LoginRequiredMixin, AddCtxMixin, UpdateView):
    model = Partner
    template_name = 'create.html'
    form_class = PartnerForm
    success_url = reverse_lazy('partners')
    context_vars = {'env': {'header': 'Обновить данные партнера', }}


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
    contract_type = Contract.ContractType.BUY

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env']['columns'][0]['url'] = 'contract_contractor_view'
        context['env']['create_url'] = 'contract_contractor_add'
        return context


class ContractContractorDetailView(ContractDetailView):
    pass


class ContractContractorCreateView(ContractCreateView):
    form_class = ContractForm
    success_url = reverse_lazy('contracts_contractor')

    def get_initial(self):
        initial = super().get_initial()
        initial['contract_type'] = Contract.ContractType.BUY
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'partner_id' in context['view'].kwargs:
            context['form'].initial['partner'] = context['view'].kwargs['partner_id']
        return context


class ContractContractorUpdateView(ContractUpdateView):
    success_url = reverse_lazy('contracts_contractor')

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
