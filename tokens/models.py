import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Doctor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    specialization = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'doctors'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.specialization}"


class Slot(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('DELAYED', 'Delayed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_capacity = models.IntegerField(validators=[MinValueValidator(1)])
    current_capacity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    delay_minutes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'slots'
        ordering = ['start_time']
        constraints = [
            models.CheckConstraint(
                check=models.Q(current_capacity__lte=models.F('max_capacity')),
                name='capacity_not_exceeded'
            )
        ]

    def __str__(self):
        return f"{self.doctor.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    @property
    def available_capacity(self):
        return self.max_capacity - self.current_capacity


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'patients'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Token(models.Model):
    CATEGORY_CHOICES = [
        ('EMERGENCY', 'Emergency'),
        ('PRIORITY_PAID', 'Priority Paid'),
        ('FOLLOWUP', 'Follow-up'),
        ('ONLINE', 'Online'),
        ('WALKIN', 'Walk-in'),
    ]

    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show'),
        ('COMPLETED', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='tokens')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='tokens')
    token_number = models.IntegerField()
    priority = models.FloatField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    estimated_time = models.DateTimeField()
    actual_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tokens'
        ordering = ['slot', 'token_number']
        unique_together = [['slot', 'token_number']]

    def __str__(self):
        return f"Token #{self.token_number} - {self.patient.name}"


class WaitingList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='waiting_list')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='waiting_list')
    category = models.CharField(max_length=20, choices=Token.CATEGORY_CHOICES)
    priority = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'waiting_list'
        ordering = ['priority', 'created_at']

    def __str__(self):
        return f"Waiting - {self.patient.name} for {self.slot}"
