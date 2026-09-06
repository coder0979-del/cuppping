def cuupping_permissions(request):
    """
    معالج سياق للتحقق التلقائي من صلاحيات المستخدم في القوالب
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {
            'is_doctor': False,
            'is_receptionist': False,
        }
    
    return {
        'is_doctor': request.user.groups.filter(name='Doctors').exists(),
        'is_receptionist': request.user.groups.filter(name='Receptionists').exists(),
    }