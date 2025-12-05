import os
import uuid
import shutil
from pathlib import Path
from django.db import models
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.db.models.signals import pre_delete
from django.dispatch import receiver


# =====================
# Helper Functions
# =====================
def delete_file(file_field):
    """Safely delete a file if it exists."""
    try:
        if file_field and hasattr(file_field, 'path') and os.path.isfile(file_field.path):
            os.remove(file_field.path)
            return True
    except Exception:
        pass
    return False


def delete_directory_if_empty(directory_path):
    """Delete directory if it's empty after file deletion."""
    try:
        if os.path.exists(directory_path) and not os.listdir(directory_path):
            os.rmdir(directory_path)
            return True
    except Exception:
        pass
    return False


# =====================
# Application Deadline Model
# =====================
class ApplicationDeadline(models.Model):
    """Model to manage application deadlines"""
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date']
        verbose_name_plural = "Application Deadlines"

    def __str__(self):
        return f"{self.name} ({self.start_date.date()} - {self.end_date.date()})"

    @property
    def is_open(self):
        """Check if application window is currently open"""
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    @property
    def days_remaining(self):
        """Get days remaining until deadline"""
        if self.is_open:
            delta = self.end_date - timezone.now()
            return delta.days
        return 0


# =====================
# Application Status Log Model
# =====================
class ApplicationStatusLog(models.Model):
    """Audit log for application status changes"""
    application = models.ForeignKey(
        'BursaryApplication',
        on_delete=models.CASCADE,
        related_name='status_logs'
    )
    old_status = models.CharField(max_length=20, null=True, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='application_status_changes'
    )
    reason = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['application', '-changed_at']),
            models.Index(fields=['-changed_at']),
        ]
        verbose_name_plural = "Application Status Logs"

    def __str__(self):
        return f"{self.application.reference_number}: {self.old_status} → {self.new_status}"


# =====================
# Bursary Application Model
# =====================
class BursaryApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    
    # =====================
    # Personal Information
    # =====================
    full_name = models.CharField(max_length=255, db_index=True)
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Male"), ("female", "Female")]
    )
    
    applicant_photo = models.FileField(
        upload_to="uploads/applicant_photos/",
        blank=True,
        null=True
    )
    
    disability = models.BooleanField(default=False)
    
    disability_proof = models.FileField(
        upload_to="uploads/disability_proof/",
        blank=True,
        null=True
    )
    
    id_number = models.CharField(max_length=50, unique=True)

    id_upload_front = models.FileField(upload_to="uploads/ids/front/")
    id_upload_back = models.FileField(upload_to="uploads/ids/back/", blank=True, null=True)

    phone_number = models.CharField(max_length=15, db_index=True)
    email = models.EmailField(max_length=255, blank=False, null=False, db_index=True)
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
    
    chief_letter = models.FileField(
        upload_to="uploads/chief_letters/",
        blank=True,
        null=True
    )

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
    institution_name = models.CharField(max_length=255, db_index=True)
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
            ("fourth-year", "Fourth Year"),
            ("fifth-year", "Fifth Year"),
            ("sixth-year", "Sixth Year"),
            ("seventh-year", "Seventh Year"),
        ]
    )
    admission_letter = models.FileField(upload_to="uploads/admission_letters/", blank=True, null=True)
    
    transcript = models.FileField(
        upload_to="uploads/transcripts/",
        blank=True,
        null=True
    )

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
    
    single_parent_proof = models.FileField(
        upload_to="uploads/single_parent_proof/",
        blank=True,
        null=True
    )
    
    deceased_single_parent_certificate = models.FileField(
        upload_to="uploads/death_certificates/",
        blank=True,
        null=True
    )
    
    orphan_sibling_proof = models.FileField(
        upload_to="uploads/orphan_proof/",
        blank=True,
        null=True
    )
    
    father_income = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("low", "Low (KSh 1,000 – 10,000)"),
            ("medium", "Medium (KSh 10,001 – 30,000)"),
            ("high", "High (KSh 30,001 – 50,000)"),
        ]
    )
    mother_income = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ("low", "Low (KSh 1,000 – 10,000)"),
            ("medium", "Medium (KSh 10,001 – 30,000)"),
            ("high", "High (KSh 30,001 – 50,000)"),
        ]
    )

    # =====================
    # Consent Fields
    # =====================
    data_consent = models.BooleanField(default=False)
    communication_consent = models.BooleanField(default=False)
    residency_confirm = models.BooleanField(default=False)
    
    # =====================
    # Confirmation
    # =====================
    confirmation = models.BooleanField(default=False)
    reference_number = models.CharField(max_length=50, unique=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    # =====================
    # Status Field
    # =====================
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

    # =====================
    # File Cleanup Methods
    # =====================
    def delete_all_files(self):
        """Delete all uploaded files associated with this application"""
        deleted_files = []
        
        # Define all file fields to delete
        file_fields = [
            (self.applicant_photo, "applicant_photo"),
            (self.disability_proof, "disability_proof"),
            (self.id_upload_front, "id_upload_front"),
            (self.id_upload_back, "id_upload_back"),
            (self.chief_letter, "chief_letter"),
            (self.admission_letter, "admission_letter"),
            (self.transcript, "transcript"),
            (self.father_death_certificate, "father_death_certificate"),
            (self.mother_death_certificate, "mother_death_certificate"),
            (self.single_parent_proof, "single_parent_proof"),
            (self.deceased_single_parent_certificate, "deceased_single_parent_certificate"),
            (self.orphan_sibling_proof, "orphan_sibling_proof"),
        ]
        
        # Delete each file
        for file_field, field_name in file_fields:
            if delete_file(file_field):
                deleted_files.append(field_name)
        
        # Clean up empty directories
        self.cleanup_empty_directories()
        
        return deleted_files
    
    def cleanup_empty_directories(self):
        """Remove any empty directories left after file deletion"""
        media_root = "media/"
        directories_to_check = set()
        
        # Collect directories from all file fields
        file_fields = [
            self.applicant_photo,
            self.disability_proof,
            self.id_upload_front,
            self.id_upload_back,
            self.chief_letter,
            self.admission_letter,
            self.transcript,
            self.father_death_certificate,
            self.mother_death_certificate,
            self.single_parent_proof,
            self.deceased_single_parent_certificate,
            self.orphan_sibling_proof,
        ]
        
        for file_field in file_fields:
            if file_field and hasattr(file_field, 'path'):
                dir_path = os.path.dirname(file_field.path)
                if dir_path.startswith(media_root):
                    directories_to_check.add(dir_path)
        
        # Try to delete each directory if empty
        for directory in sorted(directories_to_check, reverse=True):
            delete_directory_if_empty(directory)
    
    def get_file_info(self):
        """Get information about all uploaded files"""
        file_info = []
        
        file_fields = [
            (self.applicant_photo, "Applicant Photo"),
            (self.disability_proof, "Disability Proof"),
            (self.id_upload_front, "ID Front"),
            (self.id_upload_back, "ID Back"),
            (self.chief_letter, "Chief Letter"),
            (self.admission_letter, "Admission Letter"),
            (self.transcript, "Transcript"),
            (self.father_death_certificate, "Father Death Certificate"),
            (self.mother_death_certificate, "Mother Death Certificate"),
            (self.single_parent_proof, "Single Parent Proof"),
            (self.deceased_single_parent_certificate, "Deceased Single Parent Certificate"),
            (self.orphan_sibling_proof, "Orphan Sibling Proof"),
        ]
        
        for file_field, field_name in file_fields:
            if file_field:
                try:
                    size = os.path.getsize(file_field.path) if hasattr(file_field, 'path') else 0
                    file_info.append({
                        'field': field_name,
                        'filename': os.path.basename(file_field.name),
                        'size': size,
                        'path': file_field.path if hasattr(file_field, 'path') else file_field.name,
                        'exists': os.path.isfile(file_field.path) if hasattr(file_field, 'path') else False
                    })
                except:
                    file_info.append({
                        'field': field_name,
                        'filename': file_field.name,
                        'size': 0,
                        'path': '',
                        'exists': False
                    })
        
        return file_info

    # =====================
    # Override delete method
    # =====================
    def delete(self, *args, **kwargs):
        # Delete all uploaded files
        deleted_files = self.delete_all_files()
        
        # Delete associated status logs
        self.status_logs.all().delete()
        
        # Call the original delete method
        super().delete(*args, **kwargs)
        
        return deleted_files

    def __str__(self):
        return f"{self.full_name} - {self.admission_number} ({self.reference_number})"

    class Meta:
        indexes = [
            models.Index(fields=["reference_number"]),
            models.Index(fields=["ward"]),
            models.Index(fields=["submitted_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["email"]),
            models.Index(fields=["id_number"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["full_name"]),
            models.Index(fields=["institution_name"]),
            models.Index(fields=["status", "submitted_at"]),
            models.Index(fields=["ward", "status"]),
            models.Index(fields=["year_of_study", "status"]),
            models.Index(fields=["family_status", "status"]),
        ]
        ordering = ['-submitted_at']
        verbose_name_plural = "Bursary Applications"


# =====================
# Signal for Bulk Deletions
# =====================
@receiver(pre_delete, sender=BursaryApplication)
def handle_bursary_application_delete(sender, instance, **kwargs):
    """
    Handle file deletion for bulk deletes (queryset.delete()).
    This ensures files are deleted even when using bulk operations.
    """
    instance.delete_all_files()


# =====================
# Management Command Functions
# =====================
def get_orphaned_files():
    """
    Get a list of orphaned files (files in media that aren't linked to any application)
    Returns a list of file paths
    """
    from django.conf import settings
    
    media_root = settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else "media/"
    used_files = set()
    orphaned_files = []
    
    # Collect all files currently in use
    for app in BursaryApplication.objects.all().iterator(chunk_size=100):
        file_fields = [
            app.applicant_photo,
            app.disability_proof,
            app.id_upload_front,
            app.id_upload_back,
            app.chief_letter,
            app.admission_letter,
            app.transcript,
            app.father_death_certificate,
            app.mother_death_certificate,
            app.single_parent_proof,
            app.deceased_single_parent_certificate,
            app.orphan_sibling_proof,
        ]
        
        for field in file_fields:
            if field and hasattr(field, "path") and os.path.isfile(field.path):
                used_files.add(os.path.normpath(field.path))
    
    # Find orphaned files
    if os.path.exists(media_root):
        for root, dirs, files in os.walk(media_root):
            for file in files:
                file_path = os.path.normpath(os.path.join(root, file))
                if file_path not in used_files:
                    orphaned_files.append(file_path)
    
    return orphaned_files


def cleanup_orphaned_files(dry_run=False):
    """
    Delete all orphaned files
    Returns: (deleted_count, total_size_freed)
    """
    orphaned_files = get_orphaned_files()
    deleted_count = 0
    total_size = 0
    
    for file_path in orphaned_files:
        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            
            if not dry_run:
                os.remove(file_path)
                
                # Try to remove empty parent directory
                parent_dir = os.path.dirname(file_path)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    try:
                        os.rmdir(parent_dir)
                    except OSError:
                        pass
            
            deleted_count += 1
            total_size += file_size
        except Exception:
            continue
    
    return deleted_count, total_size