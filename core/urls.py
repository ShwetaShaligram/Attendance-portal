from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    ManagerListView,
    EmployeeAttendanceList,
    RegularizationCreate,
    CheckInView,
    CheckOutView,
    MyRegularizations,

    # Shared Approval Views (Manager + HR)
    ManagerRegularizationsView,
    ApproveRegularization,
    RejectRegularization,
    TeamAttendanceView,

    # HR Panel
    HRUserListView,
    HRAllRegularizationsView,
)
from .views import HREmployeeAttendanceView
from django.urls import path
from .views import AdminUserListView, AdminAttendanceView, AdminAllRegularizations
from .views import HRTodaySummaryView


urlpatterns = [
    # 🔐 Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 🧑‍💼 Manager List for Registration Dropdown
    path('managers/', ManagerListView.as_view(), name='managers'),

    # 📆 Attendance
    path('employee/attendance/', EmployeeAttendanceList.as_view(), name='employee-attendance'),
    path('employee/checkin/', CheckInView.as_view(), name='employee-checkin'),
    path('employee/checkout/', CheckOutView.as_view(), name='employee-checkout'),

    # 📩 Regularization by Employee
    path('employee/regularize/', RegularizationCreate.as_view(), name='employee-regularize'),
    path('employee/my-regularizations/', MyRegularizations.as_view(), name='employee-my-regularizations'),

    # ✅ Approval (used by Manager or HR)
    path('manager/regularizations/', ManagerRegularizationsView.as_view(), name='manager-regularizations'),
    path('manager/regularizations/<int:pk>/approve/', ApproveRegularization.as_view(), name='approve-regularization'),
    path('manager/regularizations/<int:pk>/reject/', RejectRegularization.as_view(), name='reject-regularization'),

    # 📊 Team Attendance
    path('manager/attendance/', TeamAttendanceView.as_view(), name='team-attendance'),

    # 🧑‍💼 HR Panel
    path('hr/users/', HRUserListView.as_view(), name='hr-users'),
    path('hr/regularizations/', HRAllRegularizationsView.as_view(), name='hr-regularizations'),
    path('hr/attendance/', HREmployeeAttendanceView.as_view(), name='hr-employee-attendance'),
     path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/attendance/', AdminAttendanceView.as_view(), name='admin-attendance'),
    path('admin/regularizations/', AdminAllRegularizations.as_view(), name='admin-regularizations'),
    path('hr/summary/', HRTodaySummaryView, name='hr-summary'),


]
