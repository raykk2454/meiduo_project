from django.contrib.auth import login, authenticate
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
import re
# Create your views here.
from django.urls import reverse
from django.views import View
from django import http
# from django.http import JsonResponse
from meiduo_mall.utils.response_code import RETCODE
from users.models import User
from django_redis import get_redis_connection



class LoginView(View):

    def get(self, request):
        '''
        返回登录页面
        :param request:
        :return:
        '''
        return render(request, 'login.html')

    def post(self, request):
        '''
        接收参数, 判断用户名和密码是否符合, 如果符合, 跳转到首页
        :param request:
        :return:
        '''
        # 1.接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # 2.校验
        if not all([username, password]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('用户名格式不正确')

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.HttpResponseForbidden('密码格式不正确')

        # 3.判断是否符合 authenticate
        # 4.如果符合 ===> user
        user = authenticate(username=username, password=password)

        # 5.如果不符合 没有 user对象
        if user is None:
            return  render(request, 'login.html', {'account_errmsg':'用户名或密码有误'})


        if remembered != 'on':
            # 8.如果没有勾选, 设置session有效期为0 浏览器关闭即失效
            request.session.set_expiry(0)
        else:
            # 7.判断是否勾选记住用户, 如果勾选, 设置session有效期为两周
            request.session.set_expiry(None)

        # 6.状态保持
        login(request, user)

        # 9.重定向到首页
        return redirect(reverse('contents:index'))








class MobileCountView(View):

    def get(self, request, mobile):
        '''
        判断电话是否重复, 返回对应的个数
        :param request:
        :param mobile:
        :return:
        '''
        # 1.从数据库中查询 mobile 对应的个数
        count = User.objects.filter(mobile=mobile).count()

        # 2.拼接参数, 返回
        return http.JsonResponse({'code':RETCODE.OK,
                                  'errmsg':'ok',
                                  'count':count})







class UsernameCountView(View):

    def get(self, request, username):
        '''
        判断用户名是否重复, 返回用户名对应的个数
        :param request:
        :param username:
        :return:
        '''
        count = User.objects.filter(username=username).count()

        return http.JsonResponse({'code':RETCODE.OK,
                                  'errmsg':'ok',
                                  'count':count})




class RegisterView(View):

    def get(self, request):
        '''
        返回注册页面
        :param request:
        :return:
        '''
        return render(request, 'register.html')


    def post(self, request):
        '''
        接收参数, 保存到数据库, 成功则跳转到首页
        :param request:
        :return:
        '''
        # 1.接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        sms_code_client = request.POST.get('sms_code')

        # 2.校验参数(总体 + 单个)
        # 2.1查看是否有为空的参数:
        if not all([username, password, password2, mobile, allow, sms_code_client]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('用户名为5-20位的字符串')

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码为8-20位的字符串')

        if password != password2:
            return http.HttpResponseForbidden('密码不一致')

        if not re.match(r'^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号格式不正确')

        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户同意')

        # 补充: 检验短信验证码的逻辑:
        # 链接redis, 获取链接对象
        redis_conn = get_redis_connection('verify_code')

        # 从redis取保存的短信验证码
        sms_code_server = redis_conn.get('send_sms_%s' % mobile)
        if sms_code_server is None:
            return render(request, 'register.html', {'sms_code_errmsg':'无效的短信验证码'})

        # 对比
        if sms_code_client != sms_code_server.decode():
            return render(request, 'register.html', {'sms_code_errmsg':'输入的短信验证码有误'})


        # 3.往mysql保存数据
        try:
            user = User.objects.create_user(username=username, password=password,
                                     mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg':'注册失败'})


        # 实现状态保持: session:
        login(request, user)


        # 4.返回结果, 成功则跳转到首页
        # return HttpResponse('跳转到首页没有完成')
        return redirect(reverse('contents:index'))




















