from django.shortcuts import render

# Create your views here.
from django.views import View


class IndexView(View):

    def get(self, request):
        '''
        展示首页内容
        :param request:
        :return:
        '''
        return render(request, 'index.html')