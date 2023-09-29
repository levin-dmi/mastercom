from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('projects/', projects, name='projects'),
    path('projects/add/', ProjectCreateView.as_view(), name='project_add'),
    path('projects/view/<int:project_id>/', project_view, name='project_view'),
    path('projects/update/<int:pk>/', ProjectUpdateView.as_view(), name='project_update'),
    path('projects/delete/<int:pk>/', ProjectDeleteView.as_view(), name='project_delete'),
    path('contracts/', ContractsView.as_view(), name='contracts'),
    path('contracts/add/', ContractCreateView.as_view(), name='contract_add'),
    path('contracts/add/<int:project_id>/', ContractCreateView.as_view(), name='contract_add_to_prj'),  # в проект
    path('contracts/view/<int:pk>/', ContractDetailView.as_view(), name='contract_view'),
    path('contracts/update/<str:section>/<int:pk>/', ContractUpdateView.as_view(), name='contract_update'),
    path('contracts/delete/<int:pk>/', ContractDeleteView.as_view(), name='contract_delete'),
    path('acts/', acts, name='acts'),
    path('acts/add/', ActCreateView.as_view(), name='act_add'),
    path('acts/add/<int:contract_id>/', ActCreateView.as_view(), name='act_add_to_ctr'),  # в договор
    path('acts/view/<int:act_id>/', act_view, name='act_view'),
    path('acts/update/<int:pk>/', ActUpdateView.as_view(), name='act_update'),
    path('acts/delete/<int:pk>/', ActDeleteView.as_view(), name='act_delete'),
    path('payments/', payments, name='payments'),
    path('payments/add/', PaymentCreateView.as_view(), name='payment_add'),
    path('payments/add/<int:contract_id>/', PaymentCreateView.as_view(), name='payment_add_to_ctr'),  # в договор
    path('payments/view/<int:payment_id>/', payment_view, name='payment_view'),
    path('payments/update/<int:pk>/', PaymentUpdateView.as_view(), name='payment_update'),
    path('payments/delete/<int:pk>/', PaymentDeleteView.as_view(), name='payment_delete'),
    path('analytic_contractor/', analytic_contractor, name='analytic_contractor'),
    path('partners/', PartnersView.as_view(), name='partners'),
    path('partners/add/', PartnerCreateView.as_view(), name='partner_add'),
    path('partners/view/<int:pk>/', PartnerDetailView.as_view(), name='partner_view'),
    path('partners/update/<int:pk>/', PartnerUpdateView.as_view(), name='partner_update'),
    path('partners/delete/<int:pk>/', PartnerDeleteView.as_view(), name='partner_delete'),
    path('ctr/contracts/', ContractsContractorView.as_view(), name='contracts_contractor'),
    path('ctr/contracts/view/<int:pk>/', ContractContractorDetailView.as_view(), name='contract_contractor_view'),
    path('ctr/contracts/add/', ContractContractorCreateView.as_view(), name='contract_contractor_add'),
    path('ctr/contracts/add/<int:partner_id>/', ContractCreateView.as_view(), name='contract_contracor_add_to_part'),  # к контрагенту
    # path('ctr/contracts/update/<int:pk>/', ContractUpdateView.as_view(), name='contract_contractor_update'),
]
