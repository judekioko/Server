import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from bursary.models import BursaryApplication


class Command(BaseCommand):
    help = "Deletes orphaned files (files not linked to any application)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show files that would be deleted without actually deleting them',
        )
        parser.add_argument(
            '--yes',
            action='store_true',
            help='Skip confirmation prompt',
        )
        parser.add_argument(
            '--path',
            type=str,
            help='Specific path to clean (default: all media)',
            default=''
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_confirm = options['yes']
        specific_path = options['path']
        
        media_root = settings.MEDIA_ROOT if hasattr(settings, 'MEDIA_ROOT') else "media/"
        
        if specific_path:
            if not os.path.exists(specific_path):
                self.stderr.write(f"Error: Path '{specific_path}' does not exist")
                return
            scan_root = specific_path
        else:
            scan_root = media_root
        
        self.stdout.write(f"Scanning for orphaned files in: {scan_root}")
        
        # Collect all files currently in use by applications
        used_files = set()
        
        self.stdout.write("Collecting files in use by applications...")
        
        total_applications = BursaryApplication.objects.count()
        self.stdout.write(f"Found {total_applications} applications in database")
        
        for i, app in enumerate(BursaryApplication.objects.all().iterator(chunk_size=100), 1):
            # Define all file fields to check
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
            
            if i % 100 == 0:
                self.stdout.write(f"  Processed {i}/{total_applications} applications...")
        
        self.stdout.write(f" Found {len(used_files)} files currently in use")
        
        # Find orphaned files
        orphaned_files = []
        total_orphaned_size = 0
        
        self.stdout.write(f"\nScanning directory: {scan_root}")
        
        if not os.path.exists(scan_root):
            self.stderr.write(f"Error: Directory '{scan_root}' does not exist")
            return
        
        for root, dirs, files in os.walk(scan_root):
            for file in files:
                file_path = os.path.normpath(os.path.join(root, file))
                
                # Skip if file is in use
                if file_path in used_files:
                    continue
                
                try:
                    file_size = os.path.getsize(file_path)
                    orphaned_files.append({
                        'path': file_path,
                        'size': file_size,
                        'relative': os.path.relpath(file_path, media_root)
                    })
                    total_orphaned_size += file_size
                except OSError as e:
                    self.stderr.write(f"  Warning: Could not read {file_path}: {e}")
        
        if not orphaned_files:
            self.stdout.write(" No orphaned files found!")
            return
        
        # Display summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"FOUND {len(orphaned_files)} ORPHANED FILES")
        self.stdout.write(f"Total size: {total_orphaned_size / (1024*1024):.2f} MB")
        self.stdout.write("="*60)
        
        # Show first 10 files as preview
        self.stdout.write("\nPreview of orphaned files:")
        for i, file_info in enumerate(orphaned_files[:10]):
            self.stdout.write(f"  {file_info['relative']} ({file_info['size'] / 1024:.1f} KB)")
        
        if len(orphaned_files) > 10:
            self.stdout.write(f"  ... and {len(orphaned_files) - 10} more files")
        
        # Ask for confirmation (unless dry-run or --yes)
        if not dry_run and not auto_confirm:
            self.stdout.write("\n" + "!"*60)
            response = input(f"\nDelete {len(orphaned_files)} orphaned files? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                self.stdout.write("Aborted.")
                return
        
        # Process files
        deleted_count = 0
        deleted_size = 0
        errors = []
        
        for file_info in orphaned_files:
            file_path = file_info['path']
            
            if dry_run:
                self.stdout.write(f"[DRY RUN] Would delete: {file_info['relative']}")
                deleted_count += 1
                deleted_size += file_info['size']
            else:
                try:
                    os.remove(file_path)
                    self.stdout.write(f" Deleted: {file_info['relative']}")
                    deleted_count += 1
                    deleted_size += file_info['size']
                    
                    # Try to remove empty parent directory
                    try:
                        parent_dir = os.path.dirname(file_path)
                        if not os.listdir(parent_dir):
                            os.rmdir(parent_dir)
                            self.stdout.write(f"  Removed empty directory: {os.path.relpath(parent_dir, media_root)}")
                    except OSError:
                        pass
                        
                except Exception as e:
                    error_msg = f"Error deleting {file_info['relative']}: {e}"
                    self.stderr.write(f" {error_msg}")
                    errors.append(error_msg)
        
        # Summary
        self.stdout.write("\n" + "="*60)
        if dry_run:
            self.stdout.write("DRY RUN COMPLETE")
            self.stdout.write(f"Would delete: {deleted_count} files")
            self.stdout.write(f"Would free: {deleted_size / (1024*1024):.2f} MB")
        else:
            self.stdout.write("CLEANUP COMPLETE")
            self.stdout.write(f"Deleted: {deleted_count} files")
            self.stdout.write(f"Freed: {deleted_size / (1024*1024):.2f} MB")
            
            if errors:
                self.stdout.write(f"\nEncountered {len(errors)} errors:")
                for error in errors[:5]:
                    self.stdout.write(f"  {error}")
                if len(errors) > 5:
                    self.stdout.write(f"  ... and {len(errors) - 5} more errors")
        
        # Clean up empty directories (optional)
        if not dry_run and not specific_path:
            self.cleanup_empty_dirs(media_root)
    
    def cleanup_empty_dirs(self, media_root):
        """Remove empty directories"""
        self.stdout.write("\nCleaning up empty directories...")
        removed_count = 0
        
        for root, dirs, files in os.walk(media_root, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        self.stdout.write(f"  Removed empty directory: {os.path.relpath(dir_path, media_root)}")
                        removed_count += 1
                except OSError:
                    pass
        
        if removed_count > 0:
            self.stdout.write(f" Removed {removed_count} empty directories")
