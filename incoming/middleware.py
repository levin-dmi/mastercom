# from __future__ import absolute_import, division, print_function
# from threading import local
#
# _thread_locals = local()
#
#
# def get_current_request():
#     """ returns the request object for this thread """
#     return getattr(_thread_locals, "request", None)
#
#
# def get_current_user():
#     """ returns the current user, if exist, otherwise returns None """
#     request = get_current_request()
#     if request:
#         return getattr(request, "user", None)
#
#
# class ThreadLocalMiddleware(object):
#     """ Simple middleware that adds the request object in thread local stor    age."""
#
#     def __init__(self, get_response):
#         self.get_response = get_response
#
#     def __call__(self, request):
#         return self.get_response(request)
#
#     def process_request(self, request):
#         _thread_locals.request = request
#
#     def process_response(self, request, response):
#         if hasattr(_thread_locals, 'request'):
#             del _thread_locals.request
#         return response

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from threading import local

USER_ATTR_NAME = getattr(settings, 'LOCAL_USER_ATTR_NAME', '_current_user')

_thread_locals = local()


def _do_set_current_user(user_fun):
    setattr(_thread_locals, USER_ATTR_NAME, user_fun.__get__(user_fun, local))


def _set_current_user(user=None):
    '''
    Sets current user in local thread.
    Can be used as a hook e.g. for shell jobs (when request object is not
    available).
    '''
    _do_set_current_user(lambda self: user)


class SetCurrentUser:
    def __init__(this, request):
        this.request = request

    def __enter__(this):
        _do_set_current_user(lambda self: getattr(this.request, 'user', None))

    def __exit__(this, type, value, traceback):
        _do_set_current_user(lambda self: None)


class ThreadLocalUserMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # request.user closure; asserts laziness;
        # memorization is implemented in
        # request.user (non-data descriptor)
        with SetCurrentUser(request):
            response = self.get_response(request)
        return response


def get_current_user():
    current_user = getattr(_thread_locals, USER_ATTR_NAME, None)
    if callable(current_user):
        return current_user()
    return current_user


def get_current_authenticated_user():
    current_user = get_current_user()
    if isinstance(current_user, AnonymousUser):
        return None
    return current_user
