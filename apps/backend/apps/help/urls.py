from django.urls import path
from .views import (
    HelpCategoriesView,
    HelpArticleListView,
    HelpArticleDetailView,
    HelpSearchView,
    HelpArticleFeedbackView,
    SupportRequestView,
    AdminHelpArticleListView,
    AdminHelpArticleDetailView,
    AdminHelpArticlePublishView,
    AdminHelpAnalyticsView
)

urlpatterns = [
    # Public endpoints
    path('categories/', HelpCategoriesView.as_view(), name='help-categories'),
    path('articles/', HelpArticleListView.as_view(), name='help-articles'),
    path('articles/<str:slug>/', HelpArticleDetailView.as_view(), name='help-article-detail'),
    path('search/', HelpSearchView.as_view(), name='help-search'),
    path('articles/<str:article_id>/feedback/', HelpArticleFeedbackView.as_view(), name='help-feedback'),
    path('support/', SupportRequestView.as_view(), name='support-request'),
    
    # Admin endpoints
    path('admin/articles/', AdminHelpArticleListView.as_view(), name='admin-help-articles'),
    path('admin/articles/<str:article_id>/', AdminHelpArticleDetailView.as_view(), name='admin-help-article-detail'),
    path('admin/articles/<str:article_id>/publish/', AdminHelpArticlePublishView.as_view(), name='admin-help-article-publish'),
    path('admin/analytics/', AdminHelpAnalyticsView.as_view(), name='admin-help-analytics'),
]
