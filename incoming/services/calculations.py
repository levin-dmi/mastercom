""" Модуль содержит расчеты для приложения incoming"""
import enum
from django.db.models import Q, Sum, FloatField
from incoming.models import Contract, Act, Payment
from typing import List
from decimal import Decimal

DEC0 = Decimal('0.00')
DEC1 = Decimal('1.00')
class ActStatusType(enum.Enum):
    """ Типы статусов актов """
    not_defined = None  # Не определен
    plan = 0  # запланирован
    on_sign = 1  # на подписи
    sign = 2  # подписан
    scan = 3  # есть скан
    archive = 4  # все ок, в архиве


class PaymentStatusType(enum.Enum):
    """ Типы статусов платежей """
    not_defined = None  # Не определен
    paid = 0  # Оплачен


class PrepaidType(enum.Enum):
    """ Типы условий возврата аванса """
    not_defined = -1  # Не определен
    pro_rata = 0  # Пропорционально закрытым актам КС
    first_ks = 1  # Полностью из первых КС

    @classmethod
    def _missing_(cls, value):
        return cls.not_defined

def calc_paid_from_acts(total_sum: float, prepaid: float, 
                        prepaid_type: PrepaidType, retention_percent: float, act_sum: float, ) -> float:
    """
    Метод считает размер оплаты с суммы закрытых КС по договору

    Args:
        ctr: Данные по контракту

    Returns:
        Размер оплаты, причитающийся с закрытых актов КС
    """
    if prepaid_type == PrepaidType.pro_rata:
        if total_sum == 0:
            return 0
        else:
            return act_sum - act_sum * (prepaid / total_sum + retention_percent / 100)

    if prepaid_type == PrepaidType.first_ks:
        return max(act_sum - act_sum * (retention_percent / 100) - prepaid, 0)

    if prepaid_type == PrepaidType.not_defined:
        return act_sum - act_sum * (retention_percent / 100)

def calc_paid_from_acts_d(total_sum: Decimal, prepaid: Decimal,
                        prepaid_type: PrepaidType, retention_percent: Decimal, act_sum: Decimal, ) -> Decimal:
    """
    Метод считает размер оплаты с суммы закрытых КС по договору

    Args:
        ctr: Данные по контракту

    Returns:
        Размер оплаты, причитающийся с закрытых актов КС
    """
    if prepaid_type == PrepaidType.pro_rata:
        if total_sum == 0:
            return DEC0
        else:
            return (act_sum - act_sum * (prepaid / total_sum + retention_percent / 100)).quantize(DEC1)

    if prepaid_type == PrepaidType.first_ks:
        return (max(act_sum - act_sum * (retention_percent / 100) - prepaid, DEC0)).quantize(DEC1)

    if prepaid_type == PrepaidType.not_defined:
        return (act_sum - act_sum * (retention_percent / 100)).quantize(DEC1)


class ContractAnalyticService:
    @staticmethod
    def _calc_paid_from_acts(total_sum: Decimal, prepaid: Decimal,
                              prepaid_type: PrepaidType, retention_percent: Decimal, act_sum: Decimal, ) -> Decimal:
        """
        Метод считает размер оплаты с суммы закрытых КС по договору

        Args:
            total_sum: Сумма договора
            prepaid: Сумма аванса по договору
            prepaid_type: способ удержания аванса
            retention_percent: процент гарантийных удержаний
            act_sum: сумма закрытых актов

        Returns:
            Размер оплаты, причитающийся с закрытых актов КС
        """
        if prepaid_type == PrepaidType.pro_rata:
            if total_sum == 0:
                return DEC0
            else:
                return (act_sum - act_sum * (prepaid / total_sum + retention_percent / 100)).quantize(DEC1)

        if prepaid_type == PrepaidType.first_ks:
            return (max(act_sum - act_sum * (retention_percent / 100) - prepaid, DEC0)).quantize(DEC1)

        if prepaid_type == PrepaidType.not_defined:
            return (act_sum - act_sum * (retention_percent / 100)).quantize(DEC1)


    def _calc_contract_data(self, contract_id):
        contract = Contract.objects.get(pk=contract_id)

        prepaid_type = PrepaidType(contract.prepaid_close_method.key if contract.prepaid_close_method else -1)
        total_sum = contract.total_sum or DEC0
        material_sum = contract.material_sum or DEC0
        work_sum = contract.work_sum or DEC0
        prepaid = contract.prepaid or DEC0
        retention_percent = contract.retention_percent or DEC0

        act_sum = Act.objects.aggregate(
            sum=Sum('total_sum', filter=Q(contract__pk=contract.pk)))['sum'] or DEC0
        material_act_sum = Act.objects.aggregate(
            sum=Sum('material_sum', filter=Q(contract__pk=contract.pk)))['sum'] or DEC0
        work_act_sum = Act.objects.aggregate(
            sum=Sum('work_sum', filter=Q(contract__pk=contract.pk)))['sum'] or DEC0
        pay_sum = Payment.objects.aggregate(
            sum=Sum('total_sum', filter=Q(contract__pk=contract.pk)))['sum'] or DEC0
        prepaid_pay_sum = Payment.objects.aggregate(
            sum=Sum('prepaid_sum', filter=Q(contract__pk=contract.pk)))['sum'] or DEC0
        retention_pay_sum = Payment.objects.aggregate(
            sum=Sum('retention_sum', filter=Q(contract__pk=contract.pk)))['sum'] or DEC0

        balance = []
        cashflow = []
        working = []
        if contract.can_calculated():
            balance = [act_sum, pay_sum, act_sum - pay_sum]

            paid_from_acts = self._calc_paid_from_acts(total_sum, prepaid, prepaid_type, retention_percent, act_sum)
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
                          'status_ok': True if PaymentStatusType(
                              pay.status.key) == PaymentStatusType.paid else False,
                          'total': False})
        recon.sort(key=lambda dictionary: dictionary['date'])
        total_debet = act_sum
        total_kredit = pay_sum
        recon.append({'date': '', 'doc': "Обороты по договору",
                      'debet': total_debet, 'kredit': total_kredit,
                      'status': '', 'status_ok': True, 'total': True})
        recon.append({'date': '', 'doc': "ИТОГО",
                      'debet': total_debet - total_kredit if total_debet - total_kredit > 0 else '',
                      'kredit': total_kredit - total_debet if total_debet - total_kredit <= 0 else '',
                      'status': '', 'status_ok': True, 'total': True})

        return {'balance': balance, 'cashflow': cashflow, 'working': working, 'recon': recon}


    def calculate(self, contract_id: int):
        return self._calc_contract_data(contract_id)
