"""MongoDB persistence layer"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
from pathlib import Path
import logging
import pandas as pd

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from src.persistence.config import MONGO_URI, MONGO_DB
from src.persistence.models import RunDocument, RunItemDocument, RunIssueDocument
from src.persistence.connection_pool import get_database

logger = logging.getLogger(__name__)


class RunStore:
    """Store for managing runs in MongoDB (uses connection pool)"""
    
    def __init__(self, mongo_uri: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize run store (uses shared connection pool).
        
        Args:
            mongo_uri: MongoDB connection URI (ignored - uses pool)
            db_name: Database name (ignored - uses pool)
        """
        try:
            # Use connection pool instead of creating new connections
            self.db = get_database()
            self.runs_collection: Collection = self.db["runs"]
            self.run_items_collection: Collection = self.db["run_items"]
            self.run_issues_collection: Collection = self.db["run_issues"]
            
            # Create indexes for performance (idempotent - safe to call multiple times)
            # Don't fail if indexes can't be created
            try:
                self._ensure_indexes()
            except Exception as index_error:
                logger.warning(f"Could not create indexes (non-critical): {index_error}")
        except Exception as e:
            logger.error(f"Failed to initialize RunStore: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _ensure_indexes(self):
        """Create indexes for faster queries (background creation for speed)"""
        try:
            # Create indexes in background to avoid blocking
            # Index on user_id and created_at for fast dashboard queries (most important)
            self.runs_collection.create_index(
                [("user_id", 1), ("created_at", -1)],
                background=True,
                name="user_created_idx"
            )
            # Index on run_id for fast lookups
            self.runs_collection.create_index(
                "run_id",
                background=True,
                unique=True,
                name="run_id_idx"
            )
            # Index on user_id and run_id for item/issue queries
            self.run_items_collection.create_index(
                [("user_id", 1), ("run_id", 1)],
                background=True,
                name="user_run_items_idx"
            )
            self.run_issues_collection.create_index(
                [("user_id", 1), ("run_id", 1)],
                background=True,
                name="user_run_issues_idx"
            )
            logger.debug("✅ Indexes created/verified")
        except Exception as e:
            logger.warning(f"Could not create indexes (may already exist): {e}")
    
    def close(self):
        """Close MongoDB connection (no-op with connection pool)"""
        # Don't close - connection pool manages connections
        pass
    
    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        timestamp = datetime.utcnow().isoformat()
        return f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file."""
        path = Path(file_path)
        if not path.exists():
            return ""
        
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def save_run(
        self,
        user_id: str,
        ordered_file: str,
        sold_file: str,
        mapping_file: Optional[str],
        reconciled_df: Any,  # pd.DataFrame
        issues: List[Dict[str, Any]],
        summary: Dict[str, Any],
        run_id: Optional[str] = None,
        config_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a complete run to MongoDB.
        
        Args:
            user_id: User ID who owns this run
            ordered_file: Path to ordered file
            sold_file: Path to sold file
            mapping_file: Optional path to mapping config
            reconciled_df: Reconciled DataFrame
            issues: List of issue dictionaries
            summary: Summary statistics
            run_id: Optional run ID to use (if not provided, generates one)
            
        Returns:
            Run ID
        """
        if run_id is None:
            run_id = self._generate_run_id()
        
        # Prepare input metadata
        input_metadata = {
            "ordered_file": str(Path(ordered_file).name),
            "ordered_file_path": str(Path(ordered_file).absolute()),
            "ordered_file_hash": self._compute_file_hash(ordered_file),
            "sold_file": str(Path(sold_file).name),
            "sold_file_path": str(Path(sold_file).absolute()),
            "sold_file_hash": self._compute_file_hash(sold_file),
        }
        
        if mapping_file:
            input_metadata["mapping_file"] = str(Path(mapping_file).name)
            input_metadata["mapping_file_path"] = str(Path(mapping_file).absolute())
        
        # Prepare stats
        stats = summary.copy()
        stats["total_issues"] = len(issues)
        
        # Prepare config summary
        config_summary = {
            "mapping_used": mapping_file is not None,
        }
        # Add any additional config metadata (e.g., date_from, date_to, report_name)
        if config_metadata:
            config_summary.update(config_metadata)
        
        # Create run document
        run_doc = RunDocument(
            run_id=run_id,
            user_id=user_id,
            created_at=datetime.utcnow(),
            input_metadata=input_metadata,
            stats=stats,
            config_summary=config_summary,
        )
        
        # Insert run
        try:
            run_dict = run_doc.dict(by_alias=True, exclude={"id"})  # Exclude id, let MongoDB generate it
            self.runs_collection.insert_one(run_dict)
            logger.info(f"Saved run: {run_id}")
        except PyMongoError as e:
            logger.error(f"Failed to save run: {e}")
            raise
        
        # Insert run items
        run_items = []
        for _, row in reconciled_df.iterrows():
            item = RunItemDocument(
                run_id=run_id,
                user_id=user_id,
                medicine_key=str(row.get("medicine_key", "")),
                drug_name=str(row.get("drug_name", "")) if pd.notna(row.get("drug_name")) else None,
                strength=str(row.get("strength", "")) if pd.notna(row.get("strength")) else None,
                manufacturer=str(row.get("manufacturer", "")) if pd.notna(row.get("manufacturer")) else None,
                ordered_qty=float(row.get("ordered_total", 0)),
                sold_qty=float(row.get("sold_total", 0)),
                remaining_qty=float(row.get("remaining_qty", 0)),
                shortage_qty=float(row.get("shortage_qty", 0)),
                leftover_qty=float(row.get("leftover_qty", 0)),
            )
            item_dict = item.dict(by_alias=True, exclude={"id"})  # Exclude id, let MongoDB generate it
            run_items.append(item_dict)
        
        if run_items:
            try:
                self.run_items_collection.insert_many(run_items)
                logger.info(f"Saved {len(run_items)} run items")
            except PyMongoError as e:
                logger.error(f"Failed to save run items: {e}")
                raise
        
        # Insert run issues
        run_issues = []
        for issue in issues:
            issue_doc = RunIssueDocument(
                run_id=run_id,
                user_id=user_id,
                rule_id=issue.get("rule_id", ""),
                severity=issue.get("severity", "medium"),
                medicine_key=issue.get("medicine_key"),
                details=issue.get("details", ""),
                row_ref=issue.get("row_ref", {}),
                raw_snippet=issue.get("raw_snippet", {}),
            )
            issue_dict = issue_doc.dict(by_alias=True, exclude={"id"})  # Exclude id, let MongoDB generate it
            run_issues.append(issue_dict)
        
        if run_issues:
            try:
                self.run_issues_collection.insert_many(run_issues)
                logger.info(f"Saved {len(run_issues)} run issues")
            except PyMongoError as e:
                logger.error(f"Failed to save run issues: {e}")
                raise
        
        return run_id
    
    def list_runs(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List recent runs for a user with pagination (optimized - NO count_documents to avoid slow queries).
        
        Args:
            user_id: User ID to filter runs
            limit: Maximum number of runs to return
            offset: Number of runs to skip (for pagination)
            
        Returns:
            List of run dictionaries
        """
        try:
            import time
            start_time = time.time()
            
            # Skip count_documents - it's slow and we don't need it
            # Just fetch the data directly
            
            # Use projection to only fetch needed fields (much faster)
            # Note: MongoDB doesn't allow mixing inclusion (1) and exclusion (0) in same projection
            # So we only include the fields we need
            projection = {
                "_id": 1,
                "run_id": 1,
                "created_at": 1,
                "stats": 1,
                "user_id": 1  # Include user_id for verification
            }
            
            # Use maxTimeMS to prevent long-running queries
            # Reduced timeout - if it takes longer, return empty list
            try:
                # Build query - ensure user_id is properly set
                query = {"user_id": user_id}
                logger.debug(f"Querying runs with: user_id={user_id}, limit={limit}, offset={offset}")
                
                # Fetch more documents than needed to account for filtering out empty reports
                # We'll filter and then return only the requested amount
                # Fetch 3x the limit to ensure we have enough after filtering
                fetch_limit = max(limit * 3, 30)  # At least 30, or 3x the requested limit
                
                cursor = self.runs_collection.find(
                    query,
                    projection=projection
                ).sort("created_at", -1).skip(offset).limit(fetch_limit).max_time_ms(10000).batch_size(fetch_limit)  # 10 second max
                
                # Convert cursor to list immediately
                docs = list(cursor)
                logger.debug(f"Found {len(docs)} documents from MongoDB")
            except Exception as query_error:
                # If query fails or times out, log and return empty list
                elapsed = time.time() - start_time
                logger.error(f"⚠️ Query failed/timed out after {elapsed:.3f}s: {query_error}")
                logger.error(f"   Query was: user_id={user_id}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return []
            
            # Fast conversion and filter out empty reports
            runs = []
            for doc in docs:
                try:
                    # Convert _id to string
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])
                    
                    # Convert created_at to ISO format string
                    if "created_at" in doc:
                        if isinstance(doc["created_at"], datetime):
                            doc["created_at"] = doc["created_at"].isoformat()
                        elif isinstance(doc["created_at"], str):
                            # Already a string, keep as is
                            pass
                    
                    # Ensure stats is a dict (not None)
                    if "stats" not in doc or doc["stats"] is None:
                        doc["stats"] = {}
                    
                    # Filter out empty reports (no data) - don't show in dashboard/history
                    stats = doc.get("stats", {})
                    has_data = (
                        stats.get("total_medicines", 0) > 0 or
                        stats.get("total_ordered", 0) > 0 or
                        stats.get("total_sold", 0) > 0
                    )
                    
                    # Only include reports that have data
                    if has_data:
                        runs.append(doc)
                        # Stop once we have enough reports
                        if len(runs) >= limit:
                            break
                    else:
                        logger.debug(f"⏭️ Filtering out empty report: {doc.get('run_id', 'unknown')}")
                except Exception as conv_error:
                    logger.warning(f"Error converting document: {conv_error}, doc keys: {list(doc.keys())}")
                    # Skip this document but continue
                    continue
            
            elapsed = time.time() - start_time
            if elapsed > 1.0:
                logger.warning(f"⚠️ Slow query: list_runs took {elapsed:.3f}s for user {user_id} ({len(runs)} runs)")
            else:
                logger.info(f"✅ list_runs: {elapsed:.3f}s, {len(runs)} runs for user {user_id} (requested {limit}, fetched {len(docs)}, filtered to {len(runs)})")
            
            return runs
        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(f"❌ Error in list_runs after {elapsed:.3f}s: {e}")
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            return []
    
    def count_runs(self, user_id: str) -> int:
        """
        Count total runs for a user (fast - uses estimated count or list length).
        
        Args:
            user_id: User ID to filter runs
            
        Returns:
            Total count of runs (approximate if exact count fails)
        """
        try:
            # Try fast estimated count first (if available)
            try:
                query = {"user_id": user_id}
                # Use estimated_document_count for speed (if available)
                # Otherwise use count_documents with short timeout
                count = self.runs_collection.count_documents(query, max_time_ms=3000)  # 3 second max
                logger.debug(f"✅ Counted {count} runs for user {user_id}")
                return count
            except Exception as count_error:
                # If count_documents fails, estimate from list_runs
                logger.debug(f"Count query failed, using list length: {count_error}")
                # Get a reasonable sample to estimate
                sample_runs = self.list_runs(user_id=user_id, limit=100, offset=0)
                # If we got 100, there might be more, but return at least 100
                estimated_count = max(len(sample_runs), 100) if len(sample_runs) == 100 else len(sample_runs)
                logger.debug(f"Estimated count: {estimated_count} runs")
                return estimated_count
        except Exception as e:
            logger.warning(f"⚠️ Failed to count runs for user {user_id}: {e}")
            # Return 0 on any error - better than hanging
            return 0
    
    def get_run(self, user_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific run by ID for a user.
        
        Args:
            user_id: User ID to verify ownership
            run_id: Run identifier
            
        Returns:
            Run dictionary or None if not found
        """
        try:
            doc = self.runs_collection.find_one({"run_id": run_id, "user_id": user_id})
            if doc:
                doc["_id"] = str(doc["_id"])
                if "created_at" in doc and isinstance(doc["created_at"], datetime):
                    doc["created_at"] = doc["created_at"].isoformat()
            return doc
        except PyMongoError as e:
            logger.error(f"Failed to get run: {e}")
            return None
    
    def get_run_items(self, user_id: str, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all items for a run.
        
        Args:
            user_id: User ID to verify ownership
            run_id: Run identifier
            
        Returns:
            List of run item dictionaries
        """
        try:
            cursor = self.run_items_collection.find({"run_id": run_id, "user_id": user_id})
            items = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                items.append(doc)
            return items
        except PyMongoError as e:
            logger.error(f"Failed to get run items: {e}")
            return []
    
    def get_run_issues(self, user_id: str, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all issues for a run.
        
        Args:
            user_id: User ID to verify ownership
            run_id: Run identifier
            
        Returns:
            List of run issue dictionaries
        """
        try:
            cursor = self.run_issues_collection.find({"run_id": run_id, "user_id": user_id})
            issues = []
            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                issues.append(doc)
            return issues
        except PyMongoError as e:
            logger.error(f"Failed to get run issues: {e}")
            return []
    
    def delete_run(self, user_id: str, run_id: str) -> bool:
        """
        Delete a run and all associated data (items, issues).
        Also deletes output files if they exist.
        
        Args:
            user_id: User ID to verify ownership
            run_id: Run identifier
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # First verify the run exists and belongs to the user
            run = self.runs_collection.find_one({"run_id": run_id, "user_id": user_id})
            if not run:
                logger.warning(f"Run {run_id} not found or doesn't belong to user {user_id}")
                return False
            
            # Delete run items
            items_result = self.run_items_collection.delete_many({"run_id": run_id, "user_id": user_id})
            logger.info(f"Deleted {items_result.deleted_count} run items for {run_id}")
            
            # Delete run issues
            issues_result = self.run_issues_collection.delete_many({"run_id": run_id, "user_id": user_id})
            logger.info(f"Deleted {issues_result.deleted_count} run issues for {run_id}")
            
            # Delete the run itself
            run_result = self.runs_collection.delete_one({"run_id": run_id, "user_id": user_id})
            if run_result.deleted_count > 0:
                logger.info(f"Deleted run {run_id} for user {user_id}")
                
                # Optionally delete output files
                try:
                    from pathlib import Path
                    output_base = Path("out/web_runs")
                    run_output_dir = output_base / run_id
                    if run_output_dir.exists():
                        import shutil
                        shutil.rmtree(run_output_dir)
                        logger.info(f"Deleted output directory: {run_output_dir}")
                except Exception as file_error:
                    logger.warning(f"Could not delete output files for {run_id}: {file_error}")
                    # Don't fail the deletion if file cleanup fails
                
                return True
            else:
                logger.warning(f"Run {run_id} was not deleted (may have been already deleted)")
                return False
                
        except PyMongoError as e:
            logger.error(f"Failed to delete run {run_id}: {e}")
            return False

