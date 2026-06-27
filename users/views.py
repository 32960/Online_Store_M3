from django.http import HttpResponse

def profile_mock(request):
    '''Mock profile view'''
    return HttpResponse('Profile')

def login_mock(request):
    '''Mock login view'''
    return HttpResponse('Login')
