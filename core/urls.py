from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # 段級位ボタンを押したらここへ → 即 /quiz/<level>/ へ飛ばす
    path("play/<str:level>/", views.play, name="play"),

    # 出題ページ
    path("quiz/<str:level>/", views.quiz, name="quiz"),

    # 1問ごとの●×画面
    path("feedback/<str:level>/", views.feedback, name="feedback"),

    # 結果
    path("result/<str:level>/", views.result, name="result"),

    # 中断
    path("abort/", views.abort, name="abort"),
]
