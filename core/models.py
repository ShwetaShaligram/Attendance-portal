from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from datetime import time

# ✅ Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


# ✅ Custom User Model
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('hr', 'HR'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    manager = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='employees'
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


# ✅ Attendance Model
class Attendance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    total_hours = models.FloatField(default=0.0)  # In hours

    def save(self, *args, **kwargs):
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            self.total_hours = round(delta.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)

    def is_late(self):
        # ✅ Allow check-in up to 10:05:59 AM (inclusive)
        return self.check_in.time() > time(10, 6)

    def is_regularized(self):
        return RegularizationRequest.objects.filter(
            user=self.user,
            date=self.date,
            status='approved'
        ).exists()

    def is_valid_day(self):
        if self.total_hours >= 9.0:
            if not self.is_late():
                return True
            return self.is_regularized()
        return False

    def status_color(self):
        return "green" if self.is_valid_day() else "red"

    def __str__(self):
        return f"{self.user.full_name} - {self.date}"


# ✅ Regularization Model
class RegularizationRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_regularizations'
    )

    def __str__(self):
        return f"{self.user.full_name} - {self.date} - {self.status}"
