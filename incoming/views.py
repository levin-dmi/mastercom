from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, FloatField
from .models import *
from .forms import *
from .services.calculations import *


@login_required()
def index(request):
    objs = {}
    contracts_for_analytic = Contract.objects.all()
    for ctr in contracts_for_analytic:
        if ctr.project.key not in objs:
            objs[ctr.project.key] = {'name': ctr.project, 'pk': ctr.project.pk, 'contracts': {}, 'sum': {}}

        act_sum = Act.objects.aggregate(sum=Sum('total_sum', output_field=FloatField(), filter=Q(contract__pk=ctr.pk)))[
            'sum']
        if not act_sum:
            act_sum = 0
        pay_sum = \
        Payment.objects.aggregate(sum=Sum('total_sum', output_field=FloatField(), filter=Q(contract__pk=ctr.pk)))['sum']
        if not pay_sum:
            pay_sum = 0
        prepaid_pay_sym = \
        Payment.objects.aggregate(sum=Sum('prepaid_sum', output_field=FloatField(), filter=Q(contract__pk=ctr.pk)))[
            'sum']
        if not prepaid_pay_sym:
            prepaid_pay_sym = 0

        retention_percent = 0 if not ctr.retention_percent else ctr.retention_percent
        ctr_prepaid = 0 if not ctr.prepaid else ctr.prepaid

        prepaid_type = PrepaidType(ctr.prepaid_close_method.key) if ctr.prepaid_close_method \
            else PrepaidType.not_defined

        debt_act_sum = calc_paid_from_acts(float(ctr.total_sum), float(ctr_prepaid), prepaid_type,
                                           float(retention_percent), float(act_sum)) \
                       - (pay_sum - prepaid_pay_sym)

        ctr_data = {'pk': ctr.pk,
                    'num_name': f"{ctr.number} ({ctr.name})",
                    'date': ctr.date,
                    'total_sum': int_num_with_spaces(ctr.total_sum),
                    'act_sum': int_num_with_spaces(act_sum),
                    'pay_sum': int_num_with_spaces(pay_sum),

                    'debt_act_sum': int_num_with_spaces(debt_act_sum),
                    'debt_prepaid_sum': int_num_with_spaces(float(ctr_prepaid) - prepaid_pay_sym),
                    'retention': int_num_with_spaces(act_sum * float(retention_percent) / 100),
                    }
        objs[ctr.project.key]['contracts'][ctr.pk] = ctr_data

        objs[ctr.project.key]['sum']['total_sum'] = objs[ctr.project.key]['sum'].get('total_sum', 0) + ctr.total_sum
        objs[ctr.project.key]['sum']['act_sum'] = objs[ctr.project.key]['sum'].get('act_sum', 0) + act_sum
        objs[ctr.project.key]['sum']['pay_sum'] = objs[ctr.project.key]['sum'].get('pay_sum', 0) + pay_sum
        objs[ctr.project.key]['sum']['debt_act_sum'] = objs[ctr.project.key]['sum'].get('debt_act_sum',
                                                                                        0) + debt_act_sum
        objs[ctr.project.key]['sum']['debt_prepaid_sum'] = objs[ctr.project.key]['sum'].get('debt_prepaid_sum',
                                                                                            0) + float(
            ctr_prepaid) - prepaid_pay_sym
        objs[ctr.project.key]['sum']['retention'] = objs[ctr.project.key]['sum'].get('retention', 0) + act_sum * float(
            retention_percent) / 100

    env = {'analytic_page': True, 'header': 'Аналитика'}

    for prj in objs:
        for i in objs[prj]['sum']:
            objs[prj]['sum'][i] = int_num_with_spaces(objs[prj]['sum'][i])

    context = {'objs': objs, 'env': env, }
    return render(request, 'analytic.html', context)


@login_required()
def projects(request):
    objs = Project.objects.all()
    env = {'project_page': True, 'header': 'Проекты'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'list_view.html', context)


@login_required()
def project_view(request, project_id):
    prj = Project.objects.get(pk=project_id)
    context = {'prj': prj, }
    return render(request, 'projects/project_view.html', context)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    template_name = 'projects/project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_update.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project_delete.html'
    success_url = reverse_lazy('projects')


@login_required()
def contracts(request):
    objs = Contract.objects.all()
    env = {'contract_page': True, 'header': 'Договоры'}
    context = {'objs': objs, 'env': env}
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

    balance = [act_sum, pay_sum, act_sum - pay_sum]

    paid_from_acts = calc_paid_from_acts(total_sum, prepaid, prepaid_type, retention_percent, act_sum)
    cashflow = list([[prepaid, paid_from_acts, act_sum * retention_percent / 100],
                     [prepaid_pay_sum, pay_sum - prepaid_pay_sum, 0]])
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
                      'kredit': None, 'status': act.status,
                      'status_ok': True if ActStatusType(act.status.key) == ActStatusType.archive else False,
                      'total': False})
    for pay in Payment.objects.filter(contract=contract_id):
        recon.append({'date': pay.date, 'doc': f"Платеж № {pay.number}", 'debet': None,
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
                  'debet': total_debet - total_kredit if total_debet - total_kredit > 0 else None,
                  'kredit': total_kredit - total_debet if total_debet - total_kredit <= 0 else None,
                  'status': '', 'status_ok': True, 'total': True})

    env = {'contract_page': True, 'header': f"Договор №{contract.number} от {contract.date}"}
    context = {'obj': contract, 'env': env, 'balance': balance, 'cashflow': cashflow,
               'working': working, 'recon': recon}
    return render(request, 'contracts/contract_view.html', context)


class ContractCreateView(LoginRequiredMixin, CreateView):
    template_name = 'contracts/contract_create.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'project_id' in context['view'].kwargs:
            context['form'].initial['project'] = context['view'].kwargs['project_id']
        return context


class ContractUpdateView(LoginRequiredMixin, UpdateView):
    model = Contract
    template_name = 'contracts/contract_update.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ContractDeleteView(LoginRequiredMixin, DeleteView):
    model = Contract
    template_name = 'contracts/contract_delete.html'
    success_url = reverse_lazy('contracts')


@login_required()
def acts(request):
    objs = Act.objects.all()
    env = {'act_page': True, 'header': 'Акты'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'list_view.html', context)


@login_required()
def act_view(request, act_id):
    act = Act.objects.get(pk=act_id)
    context = {'act': act, }
    return render(request, 'acts/act_view.html', context)


class ActCreateView(LoginRequiredMixin, CreateView):
    template_name = 'acts/act_create.html'
    form_class = ActForm
    success_url = reverse_lazy('acts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'contract_id' in context['view'].kwargs:
            context['form'].initial['contract'] = context['view'].kwargs['contract_id']
        return context


class ActUpdateView(LoginRequiredMixin, UpdateView):
    model = Act
    template_name = 'acts/act_update.html'
    form_class = ActForm
    success_url = reverse_lazy('acts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ActDeleteView(LoginRequiredMixin, DeleteView):
    model = Act
    template_name = 'acts/act_delete.html'
    # form_class = ActForm
    success_url = reverse_lazy('acts')

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     return context


@login_required()
def payments(request):
    objs = Payment.objects.all()
    env = {'payment_page': True, 'header': 'Оплаты'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'list_view.html', context)


@login_required()
def payment_view(request, payment_id):
    pay = Payment.objects.get(pk=payment_id)
    context = {'pay': pay, }
    return render(request, 'payments/payment_view.html', context)


class PaymentCreateView(LoginRequiredMixin, CreateView):
    template_name = 'payments/payment_create.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'contract_id' in context['view'].kwargs:
            context['form'].initial['contract'] = context['view'].kwargs['contract_id']
        return context


class PaymentUpdateView(LoginRequiredMixin, UpdateView):
    model = Payment
    template_name = 'payments/payment_update.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PaymentDeleteView(LoginRequiredMixin, DeleteView):
    model = Payment
    template_name = 'payments/payment_delete.html'
    success_url = reverse_lazy('payments')


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
