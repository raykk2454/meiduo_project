import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

from django.test import TestCase
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings


# Create your tests here.
if __name__ == '__main__':

    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                 expires_in=300)

    dict = {
        'name':'zs',
        'age':23
    }

    access_token = serializer.dumps(dict).decode()

    # token  access_token

    print(access_token)

    data = serializer.loads(access_token)

    print(data)