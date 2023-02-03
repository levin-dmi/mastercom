""" Модуль содержит расчеты для приложения incoming"""
import enum
from django.db.models import Q, Sum, FloatField
from incoming.models import Contract, Act, Payment
from typing import List


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
    not_defined = None  # Не определен
    pro_rata = 0  # Пропорционально закрытым актам КС
    first_ks = 1  # Полностью из первых КС


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
        
#
# @dataclass
# class ContractAnalytic:
#     total_sum: float
#     prepaid: float
#     retention_percent: float
#     prepaid_type: PrepaidType
#     act_sum: float
#     matherial_act_sum: float
#     work_act_sum: float
#     pay_sum: float
#     prepaid_pay_sum: float
#     balance: List[float]
#     cashflow: List[List[float]]
#
#
# class ContractAnalyticService:
#     @staticmethod
#     def _calc_paid_from_acts(ctr: ContractAnalytic) -> float:
#         """
#         Метод считает размер оплаты с суммы закрытых КС по договору
#
#         Args:
#             ctr: Данные по контракту
#
#         Returns:
#             Размер оплаты, причитающийся с закрытых актов КС
#         """
#         if ctr.prepaid_type == PrepaidType.pro_rata:
#             return ctr.act_sum - ctr.act_sum * (ctr.prepaid / ctr.total_sum + ctr.retention_percent / 100)
#
#         if ctr.prepaid_type == PrepaidType.first_ks:
#             return max(ctr.act_sum - ctr.act_sum * (ctr.retention_percent / 100) - ctr.prepaid, 0)
#
#         if ctr.prepaid_type == PrepaidType.not_defined:
#             return ctr.act_sum - ctr.act_sum * (ctr.retention_percent / 100)
#
#     @staticmethod
#     def _act_sum_for_contract(contract_pk: int, field: str) -> float:
#         act_sum = Act.objects.aggregate(sum=Sum(field,
#                                                 output_field=FloatField(),
#                                                 filter=Q(contract__pk=contract_pk)))['sum']
#         return float(act_sum or 0)
#
#     @staticmethod
#     def _payment_sum_for_contract(contract_pk: int, field: str) -> float:
#         act_sum = Payment.objects.aggregate(sum=Sum(field,
#                                                     output_field=FloatField(),
#                                                     filter=Q(contract__pk=contract_pk)))['sum']
#         return float(act_sum or 0)
#
#     def _extract_data(self, contract_pk: int) -> ContractAnalytic:
#         contract = Contract.objects.get(pk=contract_pk)
#         prepaid_type = PrepaidType(contract.prepaid_close_method.key) if contract.prepaid_close_method \
#             else PrepaidType.not_defined
#
#         return ContractAnalytic(total_sum=float(contract.total_sum or 0),
#                                 prepaid=float(contract.prepaid or 0),
#                                 prepaid_type=prepaid_type,
#                                 retention_percent=float(contract.retention_percent or 0),
#                                 act_sum=self._act_sum_for_contract(contract_pk, 'total_sum'),
#                                 matherial_act_sum=self._act_sum_for_contract(contract_pk, 'matherial_sum'),
#                                 work_act_sum=self._act_sum_for_contract(contract_pk, 'work_act_sum'),
#                                 pay_sum=self._payment_sum_for_contract(contract_pk, 'total_sum'),
#                                 prepaid_pay_sum=self._payment_sum_for_contract(contract_pk, 'prepaid_sum'),
#                                 balance=[],
#                                 cashflow=[])
#
#     def _calculate_analytic(self, contract_data: ContractAnalytic) -> ContractAnalytic:
#         contract_data.balance.extend([contract_data.act_sum,
#                                      contract_data.pay_sum,
#                                      contract_data.act_sum - contract_data.pay_sum])
#
#         contract_data.cashflow.append([contract_data.prepaid,
#                                       self._calc_paid_from_acts(contract_data), ])
#
#
#         cashflow = []
#         retention_percent = 0 if not obj.retention_percent else float(obj.retention_percent)
#         ctr_prepaid = 0 if not obj.prepaid else float(obj.prepaid)
#         need_pay_from_acts = calc_paid_from_acts(float(obj.total_sum), ctr_prepaid, retention_percent, act_sum,
#                                                  PrepaidType(obj.prepaid_close_method.key))
#         cashflow.append(
#             [ctr_prepaid, round(need_pay_from_acts, 2), round(act_sum * float(retention_percent) / 100, 2)])
#         cashflow.append([prepaid_pay_sum, round(pay_sum - prepaid_pay_sum, 2), 0])
#         cashflow.append([round(cashflow[0][0] - cashflow[1][0], 2), round(cashflow[0][1] - cashflow[1][1], 2),
#                          round(cashflow[0][2] - cashflow[1][2], 2), ])
#
#         working = []
#         ms = obj.material_sum if obj.material_sum else 0
#         mas = material_act_sum if material_act_sum else 0
#         working.append([obj.material_sum, mas, round(float(ms) - mas, 2)])
#         working.append([obj.work_sum, work_act_sum, round(float(obj.work_sum) - work_act_sum, 2)])
#         working.append([obj.total_sum - obj.material_sum - obj.work_sum,
#                         round(act_sum - material_act_sum - work_act_sum, 2),
#                         round(float(obj.total_sum - obj.material_sum - obj.work_sum) - (
#                                     act_sum - material_act_sum - work_act_sum), 2)])
#         working.append([obj.total_sum, act_sum, round(float(obj.total_sum) - act_sum, 2)])
#
#         env = {'contract_page': True, 'header': f"Договор №{obj.number} от {obj.date}"}
#         context = {'obj': obj, 'env': env, 'balance': balance, 'cashflow': cashflow, 'working': working}
#
#         return contract_data
#
#     def calculate(self, contract_pk: int):
#         contract_data = self._extract_data(contract_pk)
#         return self._calculate_analytic(contract_data)
