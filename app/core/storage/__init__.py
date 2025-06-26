"""
Storage package per la gestione dei file con MinIO.
"""

from .minio import get_minio_client

__all__ = ["get_minio_client"] 