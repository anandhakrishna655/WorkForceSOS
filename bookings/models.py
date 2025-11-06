from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ApprenticeLinks(models.Model):
    """
    Mentor-mentee relationships between workers.
    Allows experienced workers to mentor junior workers in the system.
    """
    MENTORSHIP_STATUS = [
        ('PENDING', 'Pending - Mentorship requested, awaiting approval'),
        ('ACTIVE', 'Active - Mentorship relationship is ongoing'),
        ('COMPLETED', 'Completed - Mentorship completed successfully'),
        ('TERMINATED', 'Terminated - Mentorship ended early'),
        ('REJECTED', 'Rejected - Mentorship request rejected'),
    ]

    mentor = models.ForeignKey(
        'users.WorkerProfile',
        on_delete=models.CASCADE,
        related_name='mentees',
        help_text="Mentor worker profile"
    )
    mentee = models.ForeignKey(
        'users.WorkerProfile',
        on_delete=models.CASCADE,
        related_name='mentors',
        help_text="Mentee worker profile"
    )
    status = models.CharField(
        max_length=20,
        choices=MENTORSHIP_STATUS,
        default='PENDING',
        help_text="Status of the mentorship relationship"
    )
    start_date = models.DateField(
        blank=True,
        null=True,
        help_text="When mentorship started"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="When mentorship ended"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notes about the mentorship relationship"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When mentorship was requested"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When mentorship was last updated"
    )

    class Meta:
        db_table = 'jobs_apprenticelink'
        unique_together = [['mentor', 'mentee']]  # Prevent duplicate relationships
        ordering = ['-created_at']
        verbose_name = 'Apprentice Link'
        verbose_name_plural = 'Apprentice Links'

    def __str__(self):
        return f"{self.mentor.user.email} mentoring {self.mentee.user.email}"

    def clean(self):
        """Validate that mentor and mentee are not the same person."""
        if self.mentor == self.mentee:
            raise ValidationError("A worker cannot be both mentor and mentee in the same relationship.")

    def is_active(self):
        """Check if mentorship is currently active."""
        return self.status == 'ACTIVE'

    def activate(self):
        """Activate the mentorship and set start date."""
        self.status = 'ACTIVE'
        self.start_date = timezone.now().date()
        self.save(update_fields=['status', 'start_date'])

    def complete(self):
        """Complete the mentorship and set end date."""
        self.status = 'COMPLETED'
        self.end_date = timezone.now().date()
        self.save(update_fields=['status', 'end_date'])


class Bookings(models.Model):
    """
    Booking/appointment system for client-worker interactions.
    Manages service bookings with status tracking and review functionality.
    """
    BOOKING_STATUS = [
        ('REQUESTED', 'Requested - Initial booking request'),
        ('CONFIRMED', 'Confirmed - Booking confirmed by worker'),
        ('IN_PROGRESS', 'In Progress - Work currently being performed'),
        ('COMPLETED', 'Completed - Work completed, awaiting review'),
        ('CANCELLED', 'Cancelled - Booking cancelled'),
        ('REJECTED', 'Rejected - Booking rejected by worker'),
        ('NO_SHOW', 'No Show - Client didn\'t show up'),
    ]

    client = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='client_bookings',
        help_text="Client who made the booking"
    )
    worker = models.ForeignKey(
        'users.WorkerProfile',
        on_delete=models.CASCADE,
        related_name='worker_bookings',
        help_text="Worker being booked"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the booking/job"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the work needed"
    )
    status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS,
        default='REQUESTED',
        help_text="Current status of the booking"
    )
    start_datetime = models.DateTimeField(
        help_text="Scheduled start time"
    )
    end_datetime = models.DateTimeField(
        help_text="Scheduled end time"
    )
    duration_minutes = models.PositiveIntegerField(
        help_text="Duration in minutes"
    )
    location = models.CharField(
        max_length=300,
        blank=True,
        help_text="Location where work will be performed"
    )
    is_remote = models.BooleanField(
        default=False,
        help_text="Whether this is a remote booking"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Total cost of the booking"
    )
    client_notes = models.TextField(
        blank=True,
        help_text="Notes from client"
    )
    worker_notes = models.TextField(
        blank=True,
        help_text="Notes from worker"
    )
    rating = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text="Client rating (1-5)"
    )
    review = models.TextField(
        blank=True,
        help_text="Client review text"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When booking was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When booking was last updated"
    )

    class Meta:
        db_table = 'jobs_booking'
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['worker', 'status']),
            models.Index(fields=['start_datetime']),
        ]
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'

    def __str__(self):
        return f"{self.client.email} - {self.worker.user.email} ({self.start_datetime})"

    def clean(self):
        """Validate booking data."""
        if self.end_datetime <= self.start_datetime:
            raise ValidationError("End time must be after start time.")

        if self.rating is not None and (self.rating < 1 or self.rating > 5):
            raise ValidationError("Rating must be between 1 and 5.")

    def save(self, *args, **kwargs):
        """Override save to calculate duration if not provided."""
        if self.start_datetime and self.end_datetime and not self.duration_minutes:
            self.calculate_duration()
        super().save(*args, **kwargs)

    def is_upcoming(self):
        """Check if booking is scheduled for the future."""
        return self.start_datetime > timezone.now()

    def is_past(self):
        """Check if booking end time has passed."""
        return self.end_datetime < timezone.now()

    def confirm(self):
        """Confirm the booking."""
        self.status = 'CONFIRMED'
        self.save(update_fields=['status'])

    def start_work(self):
        """Mark work as in progress."""
        self.status = 'IN_PROGRESS'
        self.save(update_fields=['status'])

    def complete(self):
        """Complete the booking."""
        self.status = 'COMPLETED'
        self.save(update_fields=['status'])

    def cancel(self):
        """Cancel the booking."""
        self.status = 'CANCELLED'
        self.save(update_fields=['status'])

    def add_rating(self, rating, review=""):
        """Add client rating and review."""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")

        self.rating = rating
        self.review = review
        self.save(update_fields=['rating', 'review'])

        # Update worker's average rating
        self.worker.update_rating()

    def calculate_duration(self):
        """Calculate duration in minutes from start and end times."""
        if self.start_datetime and self.end_datetime:
            duration = self.end_datetime - self.start_datetime
            self.duration_minutes = int(duration.total_seconds() / 60)