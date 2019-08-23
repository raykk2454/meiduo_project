
from itsdangerous import TimedJSONWebSignatureSerializer
from itsdangerous import BadData
from django.conf import settings

def generate_access_token(openid):
    '''
    把传入的openid加密为access_token
    :param openid:
    :return:
    '''


    seriaelizer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                    expires_in=300)

    dict = {
        'openid':openid
    }

    return seriaelizer.dumps(dict).decode()


def check_access_token(access_token):
    '''
    把传入的access_token解密 获取openid, 返回
    :param access_token:
    :return:
    '''
    seriaelizer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                    expires_in=300)

    try:
        data = seriaelizer.loads(access_token)
    except BadData:
        return None
    else:
        return data.get('openid')