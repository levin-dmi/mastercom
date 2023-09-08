from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from incoming.models import *
from django.utils import timezone
from django.template.loader import render_to_string
from ...services.calculations import *
from datetime import datetime, timedelta

class Command(BaseCommand):
    """
    Sends an email to the provided addresses.
    """

    help = "Sends an email to the provided addresses."

    def add_arguments(self, parser):
        parser.add_argument("emails", nargs="+")

    def handle(self, *args, **options):
        # self.stdout.write(f"send_email from: {settings.DEFAULT_FROM_EMAIL}")
        new_changes = ChangeLog.objects.filter(sent=False)
        if len(new_changes) == 0:
            return

        tz = timezone.get_default_timezone()
        email_text = \
            """Добрый вечер! 
            Последние изменения в данных учета исполнения договоров:\n\n"""
        changes = []
        for change_obj in ChangeLog.objects.filter(sent=False):
            change = (f"\n{change_obj.user} [{change_obj.changed.astimezone(tz).strftime('%d.%m.%y %H:%M')}]: "
                      f"{ChangeLog.LogAction(change_obj.action_on_model).label} в таблице {change_obj.model}\n\t\t")
            email_text += change
            for detail_name, detail in change_obj.data.items():
                change += f"{detail_name}: {detail}\t"
                email_text += f"{detail_name}: {detail}\t"
            changes.append(change)
            email_text += "\n"

        debts = []
        for ctr in Contract.objects.all():
            if not ctr.can_calculated():
                continue

            act_sum = Act.objects.aggregate(
                sum=Sum('total_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0
            pay_sum = Payment.objects.aggregate(
                sum=Sum('total_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0
            prepaid_pay_sum = Payment.objects.aggregate(
                sum=Sum('prepaid_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0
            retention_pay_sum = Payment.objects.aggregate(
                sum=Sum('retention_sum', filter=Q(contract__pk=ctr.pk)))['sum'] or DEC0

            debt_act_sum = (calc_paid_from_acts_d(ctr.total_sum,
                                                  ctr.prepaid,
                                                  PrepaidType(
                                                      ctr.prepaid_close_method.key if ctr.prepaid_close_method else -1),
                                                  ctr.retention_percent,
                                                  act_sum)
                            - pay_sum - prepaid_pay_sum - retention_pay_sum)
            debt_prepaid_sum = ctr.prepaid - prepaid_pay_sum
            retention = (act_sum * ctr.retention_percent / 100 - retention_pay_sum).quantize(DEC1)

            if debt_act_sum > 0:
                debts.append({'contract': ctr, 'sum': debt_act_sum, 'reason': 'Оплата КС2'})
            if debt_prepaid_sum > 0:
                debts.append({'contract': ctr, 'sum': debt_prepaid_sum, 'reason': 'Аванс'})
            if retention > 0 and act_sum > ctr.total_sum:
                debts.append({'contract': ctr, 'sum': retention, 'reason': 'Возврат удержаний'})

        for email in options["emails"]:
            try:
                send_mail(
                    "Изменения в данных учета исполнения договоров",
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=render_to_string('email.html', {'changes': changes, 'debts': debts})
                )
            except BaseException as e:
                pass
            else:
                for change_obj in ChangeLog.objects.filter(sent=False):
                    change_obj.sent = True
                    change_obj.save()

        ChangeLog.objects.filter(changed__lt=timezone.now()-timedelta(weeks=8), sent=True).delete()