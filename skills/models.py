from django.db import models


class Skills(models.Model):
    """
    Define available skills that workers can have.
    Skills are organized into categories and can be assigned to workers.
    """
    SKILL_CATEGORIES = [
        ('TECHNICAL', 'Technical and IT Skills'),
        ('TRADE', 'Trade Skills'),
        ('CREATIVE', 'Creative Skills'),
        ('SERVICE', 'Service Industry Skills'),
        ('PROFESSIONAL', 'Professional Services'),
        ('GENERAL', 'General Skills'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the skill"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the skill"
    )
    category = models.CharField(
        max_length=50,
        choices=SKILL_CATEGORIES,
        default='GENERAL',
        help_text="Category of the skill"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When skill was added to the system"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When skill was last updated"
    )

    class Meta:
        db_table = 'skills_skill'
        ordering = ['name']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self):
        return self.name

    def get_worker_count(self):
        """Return the number of workers who have this skill."""
        return self.skill_workers.count()


class WorkerSkills(models.Model):
    """
    Many-to-many relationship between workers and skills with proficiency levels.
    This model connects workers to their skills and includes additional information
    about their proficiency and experience with each skill.
    """
    PROFICIENCY_LEVELS = [
        ('BEGINNER', 'Beginner - Just starting out'),
        ('INTERMEDIATE', 'Intermediate - Some experience'),
        ('ADVANCED', 'Advanced - Highly skilled'),
        ('EXPERT', 'Expert - Mastery level'),
    ]

    worker = models.ForeignKey(
        'users.WorkerProfile',
        on_delete=models.CASCADE,
        related_name='worker_skills',
        help_text="Worker profile"
    )
    skill = models.ForeignKey(
        'skills.Skills',
        on_delete=models.CASCADE,
        related_name='skill_workers',
        help_text="Skill"
    )
    proficiency_level = models.CharField(
        max_length=20,
        choices=PROFICIENCY_LEVELS,
        default='BEGINNER',
        help_text="Worker's proficiency level in this skill"
    )
    years_experience = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Years of experience with this specific skill"
    )
    certification = models.CharField(
        max_length=200,
        blank=True,
        help_text="Related certification or qualification"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this skill was added to worker profile"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this skill entry was last updated"
    )

    class Meta:
        db_table = 'skills_workerskill'
        unique_together = [['worker', 'skill']]  # Prevent duplicate skill entries
        ordering = ['-proficiency_level', 'skill']
        verbose_name = 'Worker Skill'
        verbose_name_plural = 'Worker Skills'

    def __str__(self):
        return f"{self.worker.user.email} - {self.skill.name} ({self.get_proficiency_level_display()})"