from django.urls import path
from .views import SendApprovalView, QueryApprovalView, PassDownApprovalView, RejectApprovalView, ApproveApprovalView, QueryStatusView, ModifyApprovalView, ManageApprovalView, QueryReviewerView

urlpatterns = [
    path('send/', SendApprovalView.as_view(), name='send'),
    path('query/', QueryApprovalView.as_view(), name='approval-query'),
    path('pass-down/', PassDownApprovalView.as_view(), name='pass-down'),
    path('reject/', RejectApprovalView.as_view(), name='reject'),
    path('approve/', ApproveApprovalView.as_view(), name='approve'),
    path('query-status/', QueryStatusView.as_view(), name='query-status'),
    path('modify/', ModifyApprovalView.as_view(), name='approval-modify'),
    path('manage/', ManageApprovalView.as_view(), name='manage'),
    path('query-reviewer/', QueryReviewerView.as_view(), name='query-reviewer'),
]