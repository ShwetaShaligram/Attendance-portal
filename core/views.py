from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.timezone import now, make_aware, localdate
from datetime import datetime, time
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q

from .models import CustomUser, Attendance, RegularizationRequest
from .serializers import (
    RegisterSerializer,
    ManagerSerializer,
    AttendanceSerializer,
    RegularizationRequestSerializer,
    UserSerializer,
)

# ✅ Registration
class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

# ✅ Login
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                }
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# ✅ Manager dropdown
class ManagerListView(generics.ListAPIView):
    serializer_class = ManagerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return CustomUser.objects.filter(role='manager')

# ✅ Employee Attendance View
class EmployeeAttendanceList(generics.ListAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Attendance.objects.filter(user=self.request.user).order_by('-date')

# ✅ Check-In
class CheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = now().date()

        if Attendance.objects.filter(user=user, date=today).exists():
            return Response({'error': 'Already checked in today'}, status=400)

        check_in_time = now()
        office_start_naive = datetime.combine(today, time(10, 6))
        office_start = make_aware(office_start_naive)
        is_late = check_in_time > office_start

        attendance = Attendance.objects.create(user=user, date=today, check_in=check_in_time)

        return Response({
            'message': 'Check-in successful',
            'data': AttendanceSerializer(attendance).data,
            'is_late': is_late
        })

# ✅ Check-Out
class CheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        today = now().date()

        try:
            attendance = Attendance.objects.get(user=user, date=today)

            if attendance.check_out:
                return Response({'error': 'Already checked out'}, status=400)

            attendance.check_out = now()
            duration = attendance.check_out - attendance.check_in
            attendance.total_hours = round(duration.total_seconds() / 3600, 2)
            attendance.save()

            return Response({
                'message': 'Check-out successful',
                'data': AttendanceSerializer(attendance).data
            })

        except Attendance.DoesNotExist:
            return Response({'error': 'No check-in found for today'}, status=404)

# ✅ Regularization — Only EMPLOYEES can submit
class RegularizationCreate(generics.CreateAPIView):
    serializer_class = RegularizationRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != 'employee':
            raise PermissionDenied("Only employees can submit regularization requests.")
        serializer.save(user=self.request.user)

# ✅ View my own requests
class MyRegularizations(generics.ListAPIView):
    serializer_class = RegularizationRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RegularizationRequest.objects.filter(user=self.request.user).order_by('-date')

# ✅ Manager sees their team’s requests
class ManagerRegularizationsView(generics.ListAPIView):
    serializer_class = RegularizationRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RegularizationRequest.objects.filter(user__manager=self.request.user).order_by('-date')

# ✅ Shared approval logic (Manager OR HR)
def can_approve(user, reg):
    return (
        reg.user.manager == user or
        user.role == 'hr' or
        user.role == 'admin'
    )

# ✅ Approve Regularization
class ApproveRegularization(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            reg = RegularizationRequest.objects.get(pk=pk)

            if not can_approve(request.user, reg):
                raise PermissionDenied("You are not authorized to approve this request.")

            if reg.status != 'pending':
                return Response({'error': 'Already processed'}, status=400)

            reg.status = 'approved'
            reg.approved_by = request.user
            reg.save()
            return Response({'message': '✅ Request approved'})

        except RegularizationRequest.DoesNotExist:
            return Response({'error': '❌ Request not found'}, status=404)

# ✅ Reject Regularization
class RejectRegularization(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            reg = RegularizationRequest.objects.get(pk=pk)

            if not can_approve(request.user, reg):
                raise PermissionDenied("You are not authorized to reject this request.")

            if reg.status != 'pending':
                return Response({'error': 'Already processed'}, status=400)

            reg.status = 'rejected'
            reg.approved_by = request.user
            reg.save()
            return Response({'message': '❌ Request rejected'})

        except RegularizationRequest.DoesNotExist:
            return Response({'error': '❌ Request not found'}, status=404)

# ✅ Manager team attendance
class TeamAttendanceView(generics.ListAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        manager = self.request.user
        queryset = Attendance.objects.filter(user__manager=manager)

        emp = self.request.query_params.get('employee')
        date = self.request.query_params.get('date')

        if emp:
            queryset = queryset.filter(user__id=emp)
        if date:
            queryset = queryset.filter(date=date)

        return queryset.order_by('-date')

# ✅ HR views users
class HRUserListView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'hr':
            return CustomUser.objects.none()
        return CustomUser.objects.exclude(role='hr')

# ✅ HR sees all regularizations
class HRAllRegularizationsView(ListAPIView):
    serializer_class = RegularizationRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'hr':
            return RegularizationRequest.objects.none()
        return RegularizationRequest.objects.filter(user__role='employee').order_by('-date')


# ✅ HR views employee attendance
class HREmployeeAttendanceView(ListAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
    
        date = self.request.query_params.get('date')
        queryset = Attendance.objects.all()

        if user_id:
            queryset = queryset.filter(user__id=user_id)
        if date:
            queryset = queryset.filter(date=date)

        return queryset.order_by('-date')

# ✅ HR/Manager submit request to Admin
class HRManagerRegularizationCreate(generics.CreateAPIView):
    serializer_class = RegularizationRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role not in ['hr', 'manager']:
            raise PermissionDenied("Only HR or Manager can submit to Admin.")
        serializer.save(user=self.request.user)

# ✅ HR's Own Requests
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hr_my_regularizations(request):
    user = request.user
    requests = RegularizationRequest.objects.filter(user=user).order_by('-date')
    serializer = RegularizationRequestSerializer(requests, many=True)
    return Response(serializer.data)

# ✅ HR Today Summary
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def HRTodaySummaryView(request):
    if request.user.role != 'hr':
        return Response({'error': 'Unauthorized'}, status=403)

    today = localdate()
    attendances = Attendance.objects.filter(date=today)

    total_present = attendances.count()
    on_time = attendances.filter(check_in__lte=datetime.combine(today, time(9, 30))).count()
    late = attendances.filter(check_in__gt=datetime.combine(today, time(9, 30))).count()
    pending_requests = RegularizationRequest.objects.filter(status='pending').count()

    return Response({
        'present_today': total_present,
        'on_time': on_time,
        'late_arrivals': late,
        'pending_requests': pending_requests
    })

# ✅ Admin - Users
class AdminUserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'admin':
            return CustomUser.objects.none()
        return CustomUser.objects.all().order_by('id')

# ✅ Admin - Attendance
class AdminAttendanceView(generics.ListAPIView):
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'admin':
            return Attendance.objects.none()

        user_id = self.request.query_params.get('user_id')
        date = self.request.query_params.get('date')

        queryset = Attendance.objects.all()
        if user_id:
            queryset = queryset.filter(user__id=user_id)
        if date:
            queryset = queryset.filter(date=date)

        return queryset.order_by('-date')

# ✅ Admin - Regularizations
class AdminAllRegularizations(generics.ListAPIView):
    serializer_class = RegularizationRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'admin':
            return RegularizationRequest.objects.none()
        return RegularizationRequest.objects.all().order_by('-date')
