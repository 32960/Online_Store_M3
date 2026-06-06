from config.settings import SITE_NAME

def site_info(request):
    return {'site_name': SITE_NAME}