#!/usr/bin/env python3
from datetime import datetime, timezone
from typing import Dict, Any
import iso8601

class WorkorderMapper:
    """Mapper for translating between TracOS and client workorder formats"""

    @staticmethod
    def client_to_tracos(client_workorder: Dict[str, Any]) -> Dict[str, Any]:
        """Convert client workorder format to TracOS format"""

        # Map status from client boolean fields to TracOS status enum
        status = "pending"
        if client_workorder.get("isDone", False):
            status = "completed"
        elif client_workorder.get("isOnHold", False):
            status = "on_hold"
        elif client_workorder.get("isCanceled", False):
            status = "cancelled"
        elif not client_workorder.get("isPending", True):
            status = "in_progress"

        # Parse ISO dates
        created_at = WorkorderMapper._parse_iso_date(client_workorder.get("creationDate"))
        updated_at = WorkorderMapper._parse_iso_date(client_workorder.get("lastUpdateDate"))

        # Convert to TracOS format
        tracos_workorder = {
            "number": client_workorder.get("orderNo"),
            "status": status,
            "title": client_workorder.get("summary", ""),
            "description": client_workorder.get("description", ""),
            "createdAt": created_at,
            "updatedAt": updated_at,
            "deleted": client_workorder.get("isDeleted", False),
        }

        # Handle deleted workorders
        if tracos_workorder["deleted"] and "deletedDate" in client_workorder:
            tracos_workorder["deletedAt"] = WorkorderMapper._parse_iso_date(client_workorder["deletedDate"])

        return tracos_workorder

    @staticmethod
    def tracos_to_client(tracos_workorder: Dict[str, Any]) -> Dict[str, Any]:
        """Convert TracOS workorder format to client format"""

        # Map TracOS status to client boolean fields
        status_map = {
            "isPending": tracos_workorder.get("status") == "pending",
            "isDone": tracos_workorder.get("status") == "completed",
            "isOnHold": tracos_workorder.get("status") == "on_hold",
            "isCanceled": tracos_workorder.get("status") == "cancelled",
        }

        # Build client workorder
        client_workorder = {
            "orderNo": tracos_workorder.get("number"),
            "summary": tracos_workorder.get("title", ""),
            "description": tracos_workorder.get("description", ""),
            "creationDate": WorkorderMapper._format_date(tracos_workorder.get("createdAt")),
            "lastUpdateDate": WorkorderMapper._format_date(tracos_workorder.get("updatedAt")),
            "isDeleted": tracos_workorder.get("deleted", False),
            "isSynced": True,  # This is being synced now
            **status_map
        }

        # Handle deleted workorders
        if client_workorder["isDeleted"] and "deletedAt" in tracos_workorder:
            client_workorder["deletedDate"] = WorkorderMapper._format_date(tracos_workorder["deletedAt"])

        return client_workorder

    @staticmethod
    def _parse_iso_date(date_str: str) -> datetime:
        """Parse ISO 8601 date string to datetime"""
        if not date_str:
            return datetime.now(timezone.utc)

        try:
            return iso8601.parse_date(date_str)
        except (ValueError, iso8601.ParseError):
            return datetime.now(timezone.utc)

    @staticmethod
    def _format_date(date_obj) -> str:
        """Format datetime to ISO 8601 string"""
        if isinstance(date_obj, datetime):
            return date_obj.astimezone(timezone.utc).isoformat()
        else:
            return datetime.now(timezone.utc).isoformat()
