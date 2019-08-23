from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.conf import settings
# Create your views here.
from django.urls import reverse
from django.views import View
from django import http
import re
from meiduo_mall.utils.response_code import RETCODE
import logging
from django_redis import get_redis_connection
from oauth.models import OAuthQQUser
from oauth.utils import generate_access_token, check_access_token
from users.models import User

logger = logging.getLogger('django')


class QQUserView(View):

    def get(self, request):
        """

        :param request:
        :return:
        """

        code = request.GET.get('code')

        if not code:
            return http.HttpResponseForbidden('缺少必传参数')

        # 3.获取QQLoginTool框架对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 4.调用对象的方法, 发送请求给qq, 获取access_token
            access_token = oauth.get_access_token(code)

            # 5.根据 access_token 再次发送请求, 获取 openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('oath2.0请求出错')

            # 6.去保存openid的表中,获取一下, 查看有没有
        try:
            oauth_qq = OAuthQQUser.objects.get(openid=openid)
        except Exception as e:
            # 8.如果没有: 把openid加密形成: access_token 返回给前端
            access_token = generate_access_token(openid)

            context = {
                'access_token': access_token
            }

            return render(request, 'oauth_callback.html', context=context)

        else:
            user = oauth_qq.user

            # 7.如果有:  直接重定向到首页
            # 7.1 保持状态
            login(request, user)

            response = redirect(reverse('contents:index'))

            # 7.2 写入cookie值: username
            response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

            # 7.3 重定向到首页
            return response

    def post(self, request):
        '''
        接收表单传入的参数, 解析, 并且保存
        :param request:
        :return:
        '''
        # 1.接收参数(4个)
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')
        access_token = request.POST.get('access_token')

        # 2.检验(整体 + 单个)
        if not all([mobile, password, sms_code_client]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号格式不正确')

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('密码格式不正确')

        # 链接redis, 获取链接对象
        redis_conn = get_redis_connection('verify_code')

        # 从redis取值
        sms_code_server = redis_conn.get('send_sms_%s' % mobile)

        # 判断该值是否存在,如果不存在, 报错(过期)
        if sms_code_server is None:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '过期了'})

        # 对比, 如果对比不通过, 报错(输入错误)
        if sms_code_client != sms_code_server.decode():
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '输入的短信验证码有误'})

        # 3.access_token 解密: openid
        openid = check_access_token(access_token)

        if openid is None:
            return render(request, 'oauth_callback.html', {'openid_errmsg': '解密失败'})

        # 4.往两个表中保存数据(User, OAuthQQUser)
        # 5.查看User表中对应的手机号存不存在用户
        try:
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            # 7.如果不存在, 创建新的用户
            user = User.objects.create_user(username=mobile, password=password,
                                            mobile=mobile)
        else:
            # 6.如果存在, 检查密码
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或者密码有误'})

        # 8.往OAuthQQUser存入数据
        try:
            OAuthQQUser.objects.create(openid=openid, user=user)
        except Exception as e:
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': '登录失败'})

        # 9.实现状态保持
        login(request, user)

        response = redirect(reverse('contents:index'))

        # 10.设置cookie
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

        # 11. 返回首页
        return response


class QQURLView(View):

    def get(self, request):
        '''
        接收next参数, 返回qq登录的url地址
        :param request:
        :return:
        '''
        # 1.接收查询字符串参数
        next = request.GET.get('next')

        # 2.根据QQLoginTool工具, 获取对应的对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 3.调用该对象的方法, 获取对应的登录qq url
        login_url1 = oauth.get_qq_url()

        # 4.拼接参数, 返回
        return http.JsonResponse({'code': RETCODE.OK,
                                  'errmsg': 'ok',
                                  'login_url': login_url1})
