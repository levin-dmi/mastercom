from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('inc/projects/', ProjectsView.as_view(), name='projects'),
    path('inc/projects/add/', ProjectCreateView.as_view(), name='project_add'),
    path('inc/projects/view/<int:pk>/', ProjectDetailView.as_view(), name='project_view'),
    path('inc/projects/update/<int:pk>/', ProjectUpdateView.as_view(), name='project_update'),
    path('inc/projects/delete/<int:pk>/', ProjectDeleteView.as_view(), name='project_delete'),
    path('inc/contracts/', ContractsView.as_view(), name='contracts'),
    path('inc/contracts/add/', ContractCreateView.as_view(), name='contract_add'),
    path('inc/contracts/add/<int:project_id>/', ContractCreateView.as_view(), name='contract_add_to_prj'),  # в проект
    path('inc/contracts/view/<int:pk>/', ContractDetailView.as_view(), name='contract_view'),
    path('inc/contracts/update/<int:pk>/', ContractUpdateView.as_view(), name='contract_update'),
    path('inc/contracts/delete/<int:pk>/', ContractDeleteView.as_view(), name='contract_delete'),
    path('inc/acts/', ActsView.as_view(), name='acts'),
    path('inc/acts/add/', ActCreateView.as_view(), name='act_add'),
    path('inc/acts/add/<int:contract_id>/', ActCreateView.as_view(), name='act_add_to_ctr'),  # в договор
    path('inc/acts/view/<int:act_id>/', act_view, name='act_view'),
    path('inc/acts/update/<int:pk>/', ActUpdateView.as_view(), name='act_update'),
    path('inc/acts/delete/<int:pk>/', ActDeleteView.as_view(), name='act_delete'),
    path('inc/payments/', PaymentsView.as_view(), name='payments'),
    path('inc/payments/add/', PaymentCreateView.as_view(), name='payment_add'),
    path('inc/payments/add/<int:contract_id>/', PaymentCreateView.as_view(), name='payment_add_to_ctr'),  # в договор
    path('inc/payments/view/<int:pk>/', PaymentDetailView.as_view(), name='payment_view'),
    path('inc/payments/update/<int:pk>/', PaymentUpdateView.as_view(), name='payment_update'),
    path('inc/payments/delete/<int:pk>/', PaymentDeleteView.as_view(), name='payment_delete'),
    path('ctr/analytic_contractor/', analytic_contractor, name='analytic_contractor'),
    path('ctr/partners/', PartnersView.as_view(), name='partners'),
    path('ctr/partners/add/', PartnerCreateView.as_view(), name='partner_add'),
    path('ctr/partners/view/<int:pk>/', PartnerDetailView.as_view(), name='partner_view'),
    path('ctr/partners/update/<int:pk>/', PartnerUpdateView.as_view(), name='partner_update'),
    path('ctr/partners/delete/<int:pk>/', PartnerDeleteView.as_view(), name='partner_delete'),
    path('ctr/contracts/', ContractsContractorView.as_view(), name='contracts_contractor'),
    path('ctr/contracts/view/<int:pk>/', ContractContractorDetailView.as_view(), name='contract_contractor_view'),
    path('ctr/contracts/add/', ContractContractorCreateView.as_view(), name='contract_contractor_add'),
    path('ctr/contracts/add/<int:partner_id>/', ContractCreateView.as_view(), name='contract_contracor_add_to_part'),  # к контрагенту
    path('ctr/contracts/update/<int:pk>/', ContractContractorUpdateView.as_view(), name='contract_contractor_update'),
    path('ctr/contracts/delete/<int:pk>/', ContractContractorDeleteView.as_view(), name='contract_contractor_delete'),
    path('ctr/payments/', PaymentContractorView.as_view(), name='payments_contractor'),
    path('ctr/payments/add/', PaymentContractorCreateView.as_view(), name='payment_contractor_add'),
    path('ctr/payments/add/<int:contract_id>/', PaymentContractorCreateView.as_view(), name='payment_contractor_add_to_ctr'),  # в договор
    path('ctr/payments/view/<int:pk>/', PaymentContractorDetailView.as_view(), name='payment_contractor_view'),
    path('ctr/payments/update/<int:pk>/', PaymentContractorUpdateView.as_view(), name='payment_contractor_update'),
    path('ctr/payments/delete/<int:pk>/', PaynmentContractorDeleteView.as_view(), name='payment_contractor_delete'),
]
