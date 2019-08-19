import re

from django.db import DatabaseError
from django.http import JsonResponse, HttpResponse
from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from users.models import User


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request, 'register.html')

    def post(self, request):
        """
        实现用户注册
        :param request:请求对象
        :return: 注册结果
        """
        # 1. 接受参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        # TODO: sms_code没有接受

        # 2.校验参数（总体　＋　单个）
        # 2.1查看是否有为空的参数：
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传的参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('用户名为5-20位的字符串')

        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return http.HttpResponseForbidden('密码为8-20位的字符串')

        if password != password2:
            return http.HttpResponseForbidden('密码不一致')

        if not re.match(r'^1[345789]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号格式不正确')

        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户同意')


        try:
            User.objects.create_user(username=username,password=password,
                                     mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg':'注册失败'})

        return HttpResponse('跳转到首页没有完成')


class UsernameCountView(View):
    """判断用户是否重复注册"""

    def get(self, request, username):
        """
        
        :param request: 请求对象
        :param username: 用户名
        :return: json
        """
        # 获取数据库中该用户名对应个数
        count = User.objects.filter(username=username).count()
        # 拼接参数,　返回
        return JsonResponse({'code': 200, 'errmsg': 'OK', 'count': count})


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """

        :param request:请求对象
        :param mobile: 手机号
        :return: JSON
        """

        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code': 200, 'errmsg': 'OK', 'count': count})
