from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model with role-based access control.
    Extends Django's AbstractUser to add role functionality.
    """
    USER_ROLES = [
        ('ADMIN', 'System Administrator'),
        ('WORKER', 'Worker'),
        ('CLIENT', 'Client'),
    ]

    email = models.EmailField(
        unique=True,
        help_text="Email address for login"
    )
    role = models.CharField(
        max_length=20,
        choices=USER_ROLES,
        default='CLIENT',
        help_text="User role in the system"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Contact phone number"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether user account is verified"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When user account was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When user account was last updated"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users_customuser'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def is_worker(self):
        """Check if user is a worker."""
        return self.role == 'WORKER'

    def is_client(self):
        """Check if user is a client."""
        return self.role == 'CLIENT'

    def is_admin(self):
        """Check if user is an administrator."""
        return self.role == 'ADMIN'

    def __str__(self):
        return self.email


class WorkerProfile(models.Model):
    """
    Extended profile information for workers.
    One-to-one relationship with CustomUser for additional worker-specific fields.
    """
    user = models.OneToOneField(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='worker_profile',
        help_text="Associated user account"
    )
    bio = models.TextField(
        blank=True,
        help_text="Professional biography"
    )
    experience_years = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Years of professional experience"
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Hourly rate in local currency"
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Geographic location or service area"
    )
    availability = models.JSONField(
        default=dict,
        blank=True,
        help_text="Availability schedule as JSON"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Whether worker is currently accepting bookings"
    )
    profile_complete = models.BooleanField(
        default=False,
        help_text="Whether worker profile is complete"
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Average rating from clients"
    )
    total_jobs = models.PositiveIntegerField(
        default=0,
        help_text="Total completed jobs"
    )

    class Meta:
        db_table = 'users_workerprofile'
        verbose_name = 'Worker Profile'
        verbose_name_plural = 'Worker Profiles'

    def __str__(self):
        return f"{self.user.email}'s Profile"

    def update_rating(self):
        """
        Recalculate average rating from completed bookings.
        This method should be called after a booking is completed with a rating.
        """
        from bookings.models import Bookings

        completed_bookings = Bookings.objects.filter(
            worker=self,
            status='COMPLETED',
            rating__isnull=False
        )

        if completed_bookings.exists():
            total_rating = sum(booking.rating for booking in completed_bookings)
            self.rating = total_rating / completed_bookings.count()
        else:
            self.rating = None

        self.save(update_fields=['rating'])

    def mark_profile_complete(self):
        """
        Mark profile as complete when required fields are filled.
        This method checks if the essential fields for a complete profile are present.
        """
        required_fields = [
            self.bio,
            self.experience_years,
            self.hourly_rate,
            self.location
        ]

        if all(required_fields):
            self.profile_complete = True
            self.save(update_fields=['profile_complete'])

        return self.profile_complete