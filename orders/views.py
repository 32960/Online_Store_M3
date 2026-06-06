from django.http import HttpResponse

def cart_mock(request):
    '''Mock cart view'''
    return HttpResponse('Cart')
