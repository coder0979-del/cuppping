from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def reception_required(view_func):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.groups.filter(name='Receptionists').exists() or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def doctor_required(view_func):
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.groups.filter(name='Doctors').exists() or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrap