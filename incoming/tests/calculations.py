import pytest
from incoming.services.calculations import *


def test_calc_paid_from_acts():
    assert calc_paid_from_acts(ctr_total_sum=400, ctr_prepaid=100, ctr_retention_percent=10, acts_sum=200,
                               prepaid_type=PrepaidType.pro_rata) == 130

    assert calc_paid_from_acts(ctr_total_sum=400, ctr_prepaid=100, ctr_retention_percent=10, acts_sum=200,
                               prepaid_type=PrepaidType.first_ks) == 80
    assert calc_paid_from_acts(ctr_total_sum=400, ctr_prepaid=100, ctr_retention_percent=10, acts_sum=20,
                               prepaid_type=PrepaidType.first_ks) == 0
