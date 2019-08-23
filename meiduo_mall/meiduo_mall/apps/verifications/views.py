import random

from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from celery_tasks.sms.tasks import send_sms_code
from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from meiduo_mall.utils.response_code import RETCODE
from . import const
from django import http
import logging

logger = logging.getLogger('django')


class SMSCodeView(View):

    def get(self, request, mobile):
        '''
        接收手机号+uuid+图形验证码, 进行验证, 如果通过,发送短信验证码
        :param request:
        :param mobile:
        :return:
        '''
        # 3.链接redis
        redis_conn = get_redis_connection('verify_code')

        # 0. 从redis中取值:
        flag = redis_conn.get('send_flag_%s' % mobile)
        if flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR,
                                      'errmsg': '发送短信过于频繁'})
        # 1.接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.校验参数
        if not all([image_code_client, uuid]):
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR,
                                      'errmsg': '缺少必传参数'})

        # 4.从redis中取出图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR,
                                      'errmsg': '验证码过期'})

        # 5.删除redis中的图形验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)
            # logger.info(e)

        # 6.把 前端传入的和redis中的进行对比
        if image_code_client.lower() != image_code_server.decode().lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR,
                                      'errmsg': '验证码过期'})

        # 7.生成一个随机数, 作为短信验证码(6)
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)

        pl = redis_conn.pipeline()

        # 8.往redis中存储
        pl.setex('send_sms_%s' % mobile,
                 const.SMS_CODE_REDIS_EXPIRES,
                 sms_code)

        pl.setex('send_flag_%s' % mobile,
                 60,
                 1)

        # 指定管道:
        pl.execute()

        # 9.调用云通讯, 发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)
        send_sms_code.delay(mobile, sms_code)

        # 10.返回结果(json)
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': '发送成功'})

        # else:
        #     return http.JsonResponse({'code': RETCODE.OK,
        #                               'errmsg': 'ok'})


class ImageCodeView(View):

    def get(self, request, uuid):
        '''
        生成图形验证码, 保存到redis中, 另外返回图片
        :param request:
        :param uuid:
        :return:
        '''
        # 1.生成图形验证码
        text, image = captcha.generate_captcha()

        # 2.链接redis, 获取链接对象
        redis_conn = get_redis_connection('verify_code')

        # 3.利用链接对象, 保存数据到redis
        # redis_conn.setex('key', 'expire', 'value')
        redis_conn.setex('img_%s' % uuid, const.IMAGE_CODE_REDIS_EXPIRES, text)

        # 4.返回(图片)
        return http.HttpResponse(image, content_type='image/jpg')
