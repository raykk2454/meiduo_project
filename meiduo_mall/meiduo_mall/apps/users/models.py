from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
from itsdangerous import TimedJSONWebSignatureSerializer, BadData
import logging

logger = logging.getLogger('django')


class User(AbstractUser):
    # 增加一个手机号保存的字段:
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')

    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def generate_verify_url(self, email):
        """
        这是生成验证链接的有个工具类的函数
        :param email:
        :return:
        """

        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                     expires_in=600)
        dict = {
            'user_id': self.id,
            'email': email
        }

        token = serializer.dumps(dict).decode()

        verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token

        return verify_url

    @staticmethod
    def check_access_token(token):
        """
        把token解析
        :param token:
        :return:
        """
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                     expires_in=600)

        try:
            data = serializer.loads(token)
        except BadData as e:
            logger.error(e)
            return None
        else:
            user_id = data.get('user_id')
            email = data.get('email')

        try:
            user = User.objects.get(id=user_id, email=email)
        except Exception as e:
            return None
        else:
            return user
