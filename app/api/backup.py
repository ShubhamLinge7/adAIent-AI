"""
API endpoints for backup and restore functionality.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
import logging
import json
import shutil
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import config
from app.auth.dependencies import require_role
from app.auth.models import UserRole, Session
from app.auth.auth_service import AuthService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/backup/download")
async def download_backup(
    current_user: Session = Depends(require_role(UserRole.SUPERADMIN))
):
    """
    Create and download a complete backup of the system.
    Includes: user passwords, audit logs, and configuration.
    Only superadmin can perform backups.
    """
    try:
        auth_service = AuthService()
        backup_dir = Path(config.DATA_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.json"
        
        # Collect all data
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "users": auth_service.export_users(),
            "audit_logs": auth_service.get_audit_logs(limit=10000)
        }
        
        # Write backup file
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        logger.info(f"Backup created: {backup_file}")
        
        return FileResponse(
            path=backup_file,
            filename=f"adAIent_backup_{timestamp}.json",
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.post("/backup/restore")
async def restore_backup(
    backup_data: dict,
    current_user: Session = Depends(require_role(UserRole.SUPERADMIN))
):
    """
    Restore system from backup file.
    WARNING: This will overwrite existing users and logs!
    Only superadmin can restore backups.
    """
    try:
        auth_service = AuthService()
        
        # Validate backup structure
        if "users" not in backup_data or "timestamp" not in backup_data:
            raise HTTPException(status_code=400, detail="Invalid backup file format")
        
        # Restore users
        restored_users = auth_service.import_users(backup_data["users"])
        
        logger.info(f"Backup restored: {restored_users} users imported")
        
        return {
            "success": True,
            "message": f"Backup restored successfully",
            "users_restored": restored_users,
            "timestamp": backup_data.get("timestamp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")
