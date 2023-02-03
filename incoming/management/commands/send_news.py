from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from incoming.models import *
from django.utils import timezone


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
        for change_obj in ChangeLog.objects.filter(sent=False):
            email_text += f"\n{change_obj.user} [{change_obj.changed.astimezone(tz).strftime('%d.%m.%y %H:%M')}]: {LogAction[change_obj.action_on_model].value} в таблице {change_obj.model}\n\t\t"
            for detail_name, detail in change_obj.data.items():
                email_text += f"{detail_name}: {detail}\t"
            email_text += "\n"

        for email in options["emails"]:
            try:
                send_mail(
                    "Изменения в данных учета исполнения договов",
                    email_text,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
            except BaseException as e:
                pass
            else:
                for change_obj in ChangeLog.objects.filter(sent=False):
                    change_obj.sent = True
                    change_obj.save()
