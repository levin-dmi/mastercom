from django.views.generic.edit import CreateView, UpdateView, DeleteView, View
from django.views.generic.base import ContextMixin
from incoming.models import *

class LogCreateMixin(CreateView):
    """Добавление в CreateView фиксации действий по созданию новых записей.
    Во View должна быть указана переменная log_data со списком логгируемых полей"""

    log_data = []
    def form_valid(self, form):
        form.save()
        data =  {form.base_fields[k].label: str(form.cleaned_data[k]) for k in self.log_data}
        ChangeLog(model=form.Meta.model._meta.verbose_name_plural,
                  user=f"{self.request.user.first_name} {self.request.user.last_name}",
                  action_on_model=ChangeLog.LogAction.CREATE,
                  data=data).save()

        return super().form_valid(form)
class LogUpdateMixin(UpdateView):
    """Добавление в UpdateView фиксации действий по обновлению записей.
    Во View должна быть указана переменная log_data с двумя списками: логгируемые полея новой записи
    и логгируемые поля старой записми"""
    log_data = [], []

    def form_valid(self, form):
        obj = self.model.objects.get(pk=self.kwargs['pk'])
        old_data = {f"Старое значение - {obj._meta.get_field(k).verbose_name}":
                        str(getattr(obj, k)) for k in self.log_data[1]}
        form.save()
        data = {self.object._meta.get_field(k).verbose_name: str(getattr(self.object, k)) for k in self.log_data[0]}
        data.update(old_data)
        ChangeLog(model=self.object._meta.verbose_name_plural,
                  user=f"{self.request.user.first_name} {self.request.user.last_name}",
                  action_on_model=ChangeLog.LogAction.UPDATE,
                  data=data).save()

        return super().form_valid(form)

class LogDeleteMixin(DeleteView):
    """Добавление в DeleteView фиксации действий по удалению записей.
        Во View должна быть указана переменная log_data со списком логгируемых полей"""
    log_data = []

    def delete(self, *args, **kwargs):
        obj = self.get_object()
        old_data = {f"Старое значение - {obj._meta.get_field(k).verbose_name}":
                        str(getattr(obj, k)) for k in self.log_data}

        ChangeLog(model=obj._meta.verbose_name_plural,
                  user=f"{self.request.user.first_name} {self.request.user.last_name}",
                  action_on_model=ChangeLog.LogAction.DELETE,
                  data=old_data).save()

        return super().delete(*args, **kwargs)


# class AddCtxMixin(ContextMixin):
#     """Добавление переменных контекста. Если такая переменная существует в виде словаря,
#     словари объединяются. Иначе перезаписываем переменную"""
#     context_vars = {}
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         for context_var in self.context_vars:
#             if context_var in context:
#                 try:
#                     context[context_var].update(self.context_vars[context_var])
#                 except AttributeError:
#                     context[context_var] = self.context_vars[context_var]
#             else:
#                 context[context_var] = self.context_vars[context_var]
#
#         return context