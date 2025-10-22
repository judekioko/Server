from django.db import models
import uuid
from django.db import transaction

class BursaryApplication(models.Model):
    # =====================
    # Personal Information
    # =====================
    full_name = models.CharField(max_length=255)
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Male"), ("female", "Female")]
    )
    disability = models.BooleanField(default=False)
    id_number = models.CharField(max_length=50, unique=True)

    id_upload_front = models.FileField(upload_to="uploads/ids/front/")
    id_upload_back = models.FileField(upload_to="uploads/ids/back/", blank=True, null=True)

    phone_number = models.CharField(max_length=15)
    guardian_phone = models.CharField(max_length=15)
    guardian_id = models.CharField(max_length=50)

    # =====================
    # Residence Details
    # =====================
    ward = models.CharField(
        max_length=50,
        choices=[
            ("kivaa", "Kivaa"),
            ("masinga-central", "Masinga Central"),
            ("ndithini", "Ndithini"),
            ("ekalakala", "Ekalakala"),
            ("muthesya", "Muthesya"),
        ]
    )
    village = models.CharField(max_length=100)
    chief_name = models.CharField(max_length=255)
    chief_phone = models.CharField(max_length=15)
    sub_chief_name = models.CharField(max_length=255)
    sub_chief_phone = models.CharField(max_length=15)

    # =====================
    # Institution Details
    # =====================
    level_of_study = models.CharField(
        max_length=20,
        choices=[
            ("degree", "Degree"),
            ("certificate", "Certificate"),
            ("diploma", "Diploma"),
            ("artisan", "Artisan"),
        ]
    )
    institution_type = models.CharField(
        max_length=20,
        choices=[("college", "College"), ("university", "University")]
    )
    institution_name = models.CharField(max_length=255)
    admission_number = models.CharField(max_length=100)
    amount = models.PositiveIntegerField()
    mode_of_study = models.CharField(
        max_length=20,
        choices=[("full-time", "Full-time"), ("part-time", "Part-time")]
    )
    year_of_study = models.CharField(
        max_length=20,
        choices=[
            ("first-year", "First Year"),
            ("second-year", "Second Year"),
            ("third-year", "Third Year"),
            ("final-year", "Final Year"),
        ]
    )
    admission_letter = models.FileField(upload_to="uploads/admission_letters/", blank=True, null=True)

    # =====================
    # Family Details
    # =====================
    family_status = models.CharField(
        max_length=50,
        choices=[
            ("both-parents-alive", "Both Parents Alive"),
            ("single-parent", "Single Parent"),
            ("partial-orphan", "Partial Orphan"),
            ("total-orphan", "Total Orphan"),
        ]
    )
    father_death_certificate = models.FileField(
        upload_to="uploads/death_certificates/",
        blank=True,
        null=True
    )
    mother_death_certificate = models.FileField(
        upload_to="uploads/death_certificates/",
        blank=True,
        null=True
    )
    father_income = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("low", "Low (Below KSh 20,000/month)"),
            ("medium", "Medium (KSh 20,000 - 50,000/month)"),
            ("high", "High (Above KSh 50,000/month)"),
        ]
    )
    mother_income = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("low", "Low (Below KSh 20,000/month)"),
            ("medium", "Medium (KSh 20,000 - 50,000/month)"),
            ("high", "High (Above KSh 50,000/month)"),
        ]
    )

    # =====================
    # Confirmation
    # =====================
    confirmation = models.BooleanField(default=False)
    reference_number = models.CharField(max_length=50, unique=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    # =====================
    # Status Field
    # =====================
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    # =====================
    # Save Method (Safe for concurrency)
    # =====================
    def save(self, *args, **kwargs):
        if not self.reference_number:
            with transaction.atomic():
                self.reference_number = f"MNG-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.admission_number}"

    class Meta:
        indexes = [
            models.Index(fields=["reference_number"]),
            models.Index(fields=["ward"]),
            models.Index(fields=["submitted_at"]),
            models.Index(fields=["status"]),
        ]
