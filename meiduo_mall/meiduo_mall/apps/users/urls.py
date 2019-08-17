from . import views
from django.conf.urls import url

urlpatterns = [
    # 注册
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
]
