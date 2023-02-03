from django.contrib import admin
from .models import *

admin.site.register(Project)
admin.site.register(Contract)
admin.site.register(Act)
admin.site.register(Payment)
admin.site.register(PrepaidCloseMethod)
admin.site.register(ContractStatus)
admin.site.register(ActStatus)
admin.site.register(PaymentStatus)
admin.site.register(ChangeLog)
