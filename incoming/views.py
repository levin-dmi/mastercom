from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, FloatField
from .models import *
from .forms import *
from .services.calculations import *
from incoming.mixins import LogCreateMixin, LogUpdateMixin, LogDeleteMixin

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


    env = {'incoming_section': True, 'incoming_section': True, 'analytic_page': True, 'header': 'Аналитика'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'analytic.html', context)


@login_required()
def projects(request):
    objs = Project.objects.all()
    env = {'incoming_section': True, 'project_page': True, 'header': 'Проекты'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'list_view.html', context)


@login_required()
def project_view(request, project_id):
    prj = Project.objects.get(pk=project_id)
    env = {'incoming_section': True, 'project_page': True}
    context = {'env': env, 'prj': prj, }
    return render(request, 'projects/project_view.html', context)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    template_name = 'projects/project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'incoming_section': True, 'project_page': True}
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_update.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'incoming_section': True, 'project_page': True}
        return context


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project_delete.html'
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'incoming_section': True, 'project_page': True}
        context['undeleted_contracts'] = Contract.objects.filter(project=context['object'])
        return context


@login_required()
def contracts(request):
    objs = Contract.objects.filter(contract_type=Contract.ContractType.SALE)
    form_initial = {}
    if request.POST:
        if request.POST['project']:
            objs = objs.filter(project=int(request.POST['project']))
            form_initial['project'] = request.POST['project']
        if request.POST['contract']:
            objs = objs.filter(pk=int(request.POST['contract']))
            form_initial['contract'] = request.POST['contract']
    form = ListFilterForm(initial=form_initial)
    env = {'incoming_section': True, 'contract_page': True, 'header': 'Договоры'}
    context = {'objs': objs, 'env': env, 'form': form, }
    return render(request, 'list_view.html', context)


@login_required()
def contract_view(request, contract_id):
    contract = Contract.objects.get(pk=contract_id)

    prepaid_type = PrepaidType(contract.prepaid_close_method.key) if contract.prepaid_close_method \
        else PrepaidType.not_defined

    total_sum = float(contract.total_sum or 0)
    material_sum = float(contract.material_sum or 0)
    work_sum = float(contract.work_sum or 0)
    prepaid = float(contract.prepaid or 0)
    retention_percent = float(contract.retention_percent or 0)
    act_sum = act_sum_for_contract(contract_id, 'total_sum')
    material_act_sum = act_sum_for_contract(contract_id, 'material_sum')
    work_act_sum = act_sum_for_contract(contract_id, 'work_sum')
    pay_sum = payment_sum_for_contract(contract_id, 'total_sum')
    prepaid_pay_sum = payment_sum_for_contract(contract_id, 'prepaid_sum')
    retention_pay_sum = payment_sum_for_contract(contract_id, 'retention_sum')

    balance = [act_sum, pay_sum, act_sum - pay_sum]

    paid_from_acts = calc_paid_from_acts(total_sum, prepaid, prepaid_type, retention_percent, act_sum)
    cashflow = list([[prepaid, paid_from_acts, act_sum * retention_percent / 100],
                     [prepaid_pay_sum, pay_sum - prepaid_pay_sum - retention_pay_sum, retention_pay_sum]])
    cashflow.append([cashflow[0][0] - cashflow[1][0], cashflow[0][1] - cashflow[1][1],
                     cashflow[0][2] - cashflow[1][2], ])

    working = list([[material_sum, material_act_sum, material_sum - material_act_sum],
                    [work_sum, work_act_sum, work_sum - work_act_sum],
                    [total_sum - material_sum - work_act_sum,
                     act_sum - material_act_sum - work_act_sum,
                     total_sum - material_sum - work_sum - (act_sum - material_act_sum - work_act_sum)],
                    [total_sum, act_sum, total_sum - act_sum], ])

    recon = []  # Акт сверки
    for act in Act.objects.filter(contract=contract_id):
        recon.append({'date': act.date, 'doc': f"Акт № {act.number}", 'debet': act.total_sum,
                      'kredit': '', 'status': act.status,
                      'status_ok': True if ActStatusType(act.status.key) == ActStatusType.archive else False,
                      'total': False})
    for pay in Payment.objects.filter(contract=contract_id):
        recon.append({'date': pay.date, 'doc': f"Платеж № {pay.number}", 'debet': '',
                      'kredit': pay.total_sum, 'status': pay.status,
                      'status_ok': True if PaymentStatusType(pay.status.key) == PaymentStatusType.paid else False,
                      'total': False})
    recon.sort(key=lambda dictionary: dictionary['date'])
    total_debet = act_sum_for_contract(contract_id, 'total_sum')
    total_kredit = payment_sum_for_contract(contract_id, 'total_sum')
    recon.append({'date': '', 'doc': "Обороты по договору",
                  'debet': total_debet, 'kredit': total_kredit,
                  'status': '', 'status_ok': True, 'total': True})
    recon.append({'date': '', 'doc': "ИТОГО",
                  'debet': total_debet - total_kredit if total_debet - total_kredit > 0 else '',
                  'kredit': total_kredit - total_debet if total_debet - total_kredit <= 0 else '',
                  'status': '', 'status_ok': True, 'total': True})

    env = {'incoming_section': True, 'contract_page': True, 'header': f"Договор №{contract.number} от {contract.date}"}
    context = {'obj': contract, 'env': env, 'balance': balance, 'cashflow': cashflow,
               'working': working, 'recon': recon}
    return render(request, 'contracts/contract_view.html', context)


class ContractCreateView(LoginRequiredMixin, LogCreateMixin, CreateView):
    template_name = 'contracts/contract_create.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')
    log_data = ['number', 'date', 'total_sum']


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].initial['contract_type'] = Contract.ContractType.SALE
        context['env'] = {'incoming_section': True, 'contract_page': True}
        if 'project_id' in context['view'].kwargs:
            context['form'].initial['project'] = context['view'].kwargs['project_id']
        return context


class ContractUpdateView(LoginRequiredMixin, LogUpdateMixin, UpdateView):
    model = Contract
    template_name = 'contracts/contract_update.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')
    log_data = ['number', 'date', 'total_sum'], ['total_sum']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'incoming_section': True, 'contract_page': True}
        return context


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
        context['env'] = {'incoming_section': True, 'contract_page': True}
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
    env = {'incoming_section': True, 'act_page': True, 'header': 'Акты'}
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
    env = {'incoming_section': True, 'act_page': True}
    context = {'env': env, 'act': act, 'calc': calc}
    return render(request, 'acts/act_view.html', context)


class ActCreateView(LoginRequiredMixin, LogCreateMixin, CreateView):
    template_name = 'acts/act_create.html'
    form_class = ActForm
    success_url = reverse_lazy('acts')
    log_data = ['number', 'date', 'total_sum']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'incoming_section': True, 'act_page': True}
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'incoming_section': True, 'act_page': True}
        return context


class ActDeleteView(LoginRequiredMixin, LogDeleteMixin, DeleteView):
    model = Act
    template_name = 'acts/act_delete.html'
    # form_class = ActForm
    success_url = reverse_lazy('acts')
    log_data = ['number', 'date', 'total_sum']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'incoming_section': True, 'act_page': True}
        return context


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
    env = {'incoming_section': True, 'payment_page': True, 'header': 'Оплаты', }
    context = {'objs': objs, 'env': env, 'form': form, }
    return render(request, 'list_view.html', context)


@login_required()
def payment_view(request, payment_id):
    pay = Payment.objects.get(pk=payment_id)
    env = {'incoming_section': True, 'payment_page': True}
    context = {'env': env, 'pay': pay, }
    return render(request, 'payments/payment_view.html', context)


class PaymentCreateView(LoginRequiredMixin, LogCreateMixin, CreateView):
    template_name = 'payments/payment_create.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')
    log_data = ['number', 'date', 'total_sum']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].initial['status'] = PaymentStatus.objects.get(key=PaymentStatusType.paid.value)
        context['env'] = {'incoming_section': True, 'payment_page': True}
        if 'contract_id' in context['view'].kwargs:
            context['form'].initial['contract'] = context['view'].kwargs['contract_id']
        return context


class PaymentUpdateView(LoginRequiredMixin, LogUpdateMixin, UpdateView):
    model = Payment
    template_name = 'payments/payment_update.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')
    log_data = ['number', 'date', 'total_sum'], ['total_sum']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'incoming_section': True, 'payment_page': True}
        return context


class PaymentDeleteView(LoginRequiredMixin, LogDeleteMixin, DeleteView):
    model = Payment
    template_name = 'payments/payment_delete.html'
    success_url = reverse_lazy('payments')
    log_data = ['number', 'date', 'total_sum']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'incoming_section': True, 'payment_page': True}
        return context


class PartnerDetailView(LoginRequiredMixin, DetailView):
    model = Partner
    template_name = 'partners/partner_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'contractor_section': True, 'partner_page': True, 'header': context['object']}
        return context


class PartnersView(LoginRequiredMixin, ListView):
    template_name = 'list_view2.html'
    context_object_name = 'objs'

    def get_queryset(self):
        return Partner.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'contractor_section': True,
                          'partner_page': True,
                          'header': 'Партнеры',
                          'create_url': 'partner_add',
                          'update_url': 'partner_update',
                          'delete_url': 'partner_delete',
                          'table_headers': ['ИНН', 'Наименование'],
                          'columns': [{'name': 'inn', 'url': 'partner_view'},
                                      {'name': 'name'}],
                          }
        return context


class PartnerCreateView(LoginRequiredMixin, CreateView):
    template_name = 'create.html'
    form_class = PartnerForm
    success_url = reverse_lazy('partners')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'contractor_section': True, 'partner_page': True, 'header': 'Новый партнер'}
        return context


class PartnerUpdateView(LoginRequiredMixin, UpdateView):
    model = Partner
    template_name = 'create.html'
    form_class = PartnerForm
    success_url = reverse_lazy('partners')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'contractor_section': True, 'partner_page': True, 'header': 'Обновить данные партнера'}
        return context


class PartnerDeleteView(LoginRequiredMixin, DeleteView):
    model = Partner
    template_name = 'partners/partner_delete.html'
    success_url = reverse_lazy('partners')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['env'] = {'contractor_section': True, 'partner_page': True, 'header': 'Удалить партнера'}
        context['undeleted_contracts'] = Contract.objects.filter(partner=context['object'])
        return context


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
