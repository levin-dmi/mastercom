from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, FloatField
from .models import *
from .forms import *


def index(request):
    # objs = {'Project1': {'contracts': {'Contract1': {'number': 02/22}, {'sum': 2000000}, 'Contract2': {'sum': 100000}, },
    #                      'sum': {'sum': 100000},
    #                      'name': 'Проект 1'
    #                      },}

    objs = {}
    contracts_for_analytic = Contract.objects.all()
    for ctr in contracts_for_analytic:
        if ctr.project.key not in objs:
            objs[ctr.project.key] = {'name': ctr.project, 'contracts': {}, 'sum': {}}

        act_sum = Act.objects.aggregate(sum=Sum('total_sum', output_field=FloatField(), filter=Q(contract__pk=ctr.pk)))['sum']
        if not act_sum:
            act_sum = 0
        pay_sum = Payment.objects.aggregate(sum=Sum('total_sum', output_field=FloatField(), filter=Q(contract__pk=ctr.pk)))['sum']
        if not pay_sum:
            pay_sum = 0
        prepaid_pay_sym = Payment.objects.aggregate(sum=Sum('prepaid_sum', output_field=FloatField(), filter=Q(contract__pk=ctr.pk)))['sum']
        if not prepaid_pay_sym:
            prepaid_pay_sym = 0

        retention_percent = 0 if not ctr.retention_percent else ctr.retention_percent
        ctr_prepaid = 0 if not ctr.prepaid else ctr.prepaid

        payment_proportion = float(1 - float(ctr_prepaid)/float(ctr.total_sum) - float(retention_percent)/100)

        ctr_data = {'pk': ctr.pk,
                    'num_name': f"{ctr.number} ({ctr.name})",
                    'date': ctr.date,
                    'total_sum': int_num_with_spaces(ctr.total_sum),
                    'act_sum': int_num_with_spaces(act_sum),
                    'pay_sum': int_num_with_spaces(pay_sum),
                    'debt_act_sum': int_num_with_spaces(act_sum*payment_proportion - (pay_sum - prepaid_pay_sym)),
                    'debt_prepaid_sum': int_num_with_spaces(float(ctr_prepaid) - prepaid_pay_sym),
                    'retention': int_num_with_spaces(act_sum*float(retention_percent)/100),
                    }
        objs[ctr.project.key]['contracts'][ctr.pk] = ctr_data

        objs[ctr.project.key]['sum']['total_sum'] = objs[ctr.project.key]['sum'].get('total_sum', 0) + ctr.total_sum
        objs[ctr.project.key]['sum']['act_sum'] = objs[ctr.project.key]['sum'].get('act_sum', 0) + act_sum
        objs[ctr.project.key]['sum']['pay_sum'] = objs[ctr.project.key]['sum'].get('pay_sum', 0) + pay_sum
        objs[ctr.project.key]['sum']['debt_act_sum'] = objs[ctr.project.key]['sum'].get('debt_act_sum', 0) + act_sum*payment_proportion - (pay_sum - prepaid_pay_sym)
        objs[ctr.project.key]['sum']['debt_prepaid_sum'] = objs[ctr.project.key]['sum'].get('debt_prepaid_sum', 0) + float(ctr_prepaid) - prepaid_pay_sym
        objs[ctr.project.key]['sum']['retention'] = objs[ctr.project.key]['sum'].get('retention', 0) + act_sum*float(retention_percent)/100


    env = {'analytic_page': True, 'header': 'Аналитика'}

    for prj in objs:
        for i in objs[prj]['sum']:
            objs[prj]['sum'][i] = int_num_with_spaces(objs[prj]['sum'][i])

    context = {'objs': objs, 'env': env, }
    return render(request, 'analytic.html', context)


def projects(request):
    objs = Project.objects.all()
    env = {'project_page': True, 'header': 'Проекты'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'list_view.html', context)


def project_view(request, project_id):
    prj = Project.objects.get(pk=project_id)
    context = {'prj': prj, }
    return render(request, 'projects/project_view.html', context)


class ProjectCreateView(CreateView):
    template_name = 'projects/project_create.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProjectUpdateView(UpdateView):
    model = Project
    template_name = 'projects/project_update.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProjectDeleteView(DeleteView):
    model = Project
    template_name = 'projects/project_delete.html'
    form_class = ProjectForm
    success_url = reverse_lazy('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    
def contracts(request):
    objs = Contract.objects.all()
    env = {'contract_page': True, 'header': 'Договоры'}
    context = {'objs': objs, 'env': env}
    return render(request, 'list_view.html', context)


# ------------------------------------------------------------------------
def contract_view(request, contract_id):
    obj = Contract.objects.get(pk=contract_id)

    env = {'contract_page': True, 'header': f"Договор №{obj.number} от {obj.date}"}
    context = {'obj': obj, 'env': env}
    return render(request, 'contracts/contract_view.html', context)


class ContractCreateView(CreateView):
    template_name = 'contracts/contract_create.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ContractUpdateView(UpdateView):
    model = Contract
    template_name = 'contracts/contract_update.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ContractDeleteView(DeleteView):
    model = Contract
    template_name = 'contracts/contract_delete.html'
    form_class = ContractForm
    success_url = reverse_lazy('contracts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    

def acts(request):
    objs = Act.objects.all()
    env = {'act_page': True, 'header': 'Акты'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'list_view.html', context)


def act_view(request, act_id):
    act = Act.objects.get(pk=act_id)
    context = {'act': act, }
    return render(request, 'acts/act_view.html', context)


class ActCreateView(CreateView):
    template_name = 'acts/act_create.html'
    form_class = ActForm
    success_url = reverse_lazy('acts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ActUpdateView(UpdateView):
    model = Act
    template_name = 'acts/act_update.html'
    form_class = ActForm
    success_url = reverse_lazy('acts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ActDeleteView(DeleteView):
    model = Act
    template_name = 'acts/act_delete.html'
    form_class = ActForm
    success_url = reverse_lazy('acts')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


def payments(request):
    objs = Payment.objects.all()
    env = {'payment_page': True, 'header': 'Оплаты'}
    context = {'objs': objs, 'env': env, }
    return render(request, 'list_view.html', context)


def payment_view(request, payment_id):
    pay = Payment.objects.get(pk=payment_id)
    context = {'pay': pay, }
    return render(request, 'payments/payment_view.html', context)


class PaymentCreateView(CreateView):
    template_name = 'payments/payment_create.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PaymentUpdateView(UpdateView):
    model = Payment
    template_name = 'payments/payment_update.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PaymentDeleteView(DeleteView):
    model = Payment
    template_name = 'payments/payment_delete.html'
    form_class = PaymentForm
    success_url = reverse_lazy('payments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context