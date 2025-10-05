"""
Database management for WhisperX Cloud Run Microservice
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """SQLite database manager for job storage and retrieval"""
    
    def __init__(self, db_path: str = "whisperx_jobs.db"):
        """Initialize database manager"""
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create jobs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS jobs (
                        job_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        filename TEXT,
                        model_size TEXT DEFAULT 'large-v2',
                        enable_diarization BOOLEAN DEFAULT 1,
                        enable_alignment BOOLEAN DEFAULT 1,
                        language TEXT,
                        processing_time REAL,
                        audio_duration REAL,
                        confidence REAL,
                        error_message TEXT,
                        result_data TEXT
                    )
                """)
                
                # Create speaker_segments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS speaker_segments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT NOT NULL,
                        speaker TEXT NOT NULL,
                        start_time REAL NOT NULL,
                        end_time REAL NOT NULL,
                        text TEXT NOT NULL,
                        FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
                    )
                """)
                
                # Create word_segments table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS word_segments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT NOT NULL,
                        word TEXT NOT NULL,
                        start_time REAL NOT NULL,
                        end_time REAL NOT NULL,
                        speaker TEXT,
                        confidence REAL,
                        FOREIGN KEY (job_id) REFERENCES jobs (job_id) ON DELETE CASCADE
                    )
                """)
                
                conn.commit()
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            raise
    
    def create_job(self, job_data: Dict[str, Any]) -> bool:
        """Create a new job in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO jobs (
                        job_id, filename, model_size, enable_diarization, 
                        enable_alignment, language
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    job_data["job_id"],
                    job_data["filename"],
                    job_data.get("model_size", "large-v2"),
                    job_data.get("enable_diarization", True),
                    job_data.get("enable_alignment", True),
                    job_data.get("language")
                ))
                
                conn.commit()
                logger.info("Job created in database", job_id=job_data["job_id"])
                return True
                
        except Exception as e:
            logger.error(f"Failed to create job: {str(e)}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM jobs WHERE job_id = ?
                """, (job_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {str(e)}")
            return None
    
    def get_jobs(self, limit: int = 10, offset: int = 0, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get jobs with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM jobs"
                params = []
                
                if status:
                    query += " WHERE status = ?"
                    params.append(status)
                
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get jobs: {str(e)}")
            return []
    
    def update_job_status(self, job_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update job status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if error_message:
                    cursor.execute("""
                        UPDATE jobs SET status = ?, error_message = ?, updated_at = ?
                        WHERE job_id = ?
                    """, (status, error_message, datetime.utcnow(), job_id))
                else:
                    cursor.execute("""
                        UPDATE jobs SET status = ?, updated_at = ?
                        WHERE job_id = ?
                    """, (status, datetime.utcnow(), job_id))
                
                conn.commit()
                logger.info("Job status updated", job_id=job_id, status=status)
                return True
                
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
            return False
    
    def save_job_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Save complete job result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update main job record
                cursor.execute("""
                    UPDATE jobs SET 
                        status = ?, 
                        processing_time = ?, 
                        audio_duration = ?, 
                        language = ?, 
                        confidence = ?, 
                        result_data = ?,
                        updated_at = ?
                    WHERE job_id = ?
                """, (
                    "completed",
                    result.get("processing_time"),
                    result.get("duration"),
                    result.get("language"),
                    result.get("confidence"),
                    json.dumps(result),
                    datetime.utcnow(),
                    job_id
                ))
                
                # Save speaker segments
                if "speaker_segments" in result:
                    for segment in result["speaker_segments"]:
                        cursor.execute("""
                            INSERT INTO speaker_segments (
                                job_id, speaker, start_time, end_time, text
                            ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            job_id,
                            segment.get("speaker", "UNKNOWN"),
                            segment.get("start", 0),
                            segment.get("end", 0),
                            segment.get("text", "")
                        ))
                
                # Save word segments
                if "word_segments" in result:
                    for word in result["word_segments"]:
                        cursor.execute("""
                            INSERT INTO word_segments (
                                job_id, word, start_time, end_time, speaker, confidence
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            job_id,
                            word.get("word", ""),
                            word.get("start", 0),
                            word.get("end", 0),
                            word.get("speaker", "UNKNOWN"),
                            word.get("confidence", 0.8)
                        ))
                
                conn.commit()
                logger.info("Job result saved to database", job_id=job_id)
                return True
                
        except Exception as e:
            logger.error(f"Failed to save job result: {str(e)}")
            return False
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total jobs
                cursor.execute("SELECT COUNT(*) FROM jobs")
                total_jobs = cursor.fetchone()[0]
                
                # Jobs by status
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM jobs 
                    GROUP BY status
                """)
                jobs_by_status = dict(cursor.fetchall())
                
                # Average processing time
                cursor.execute("""
                    SELECT AVG(processing_time) 
                    FROM jobs 
                    WHERE status = 'completed' AND processing_time IS NOT NULL
                """)
                avg_processing_time = cursor.fetchone()[0] or 0.0
                
                # Recent jobs (last 24 hours)
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM jobs 
                    WHERE created_at >= datetime('now', '-1 day')
                """)
                recent_jobs = cursor.fetchone()[0]
                
                return {
                    "total_jobs": total_jobs,
                    "jobs_by_status": jobs_by_status,
                    "avg_processing_time": avg_processing_time,
                    "recent_jobs_24h": recent_jobs
                }
        except Exception as e:
            logger.error("Failed to get job stats", error=str(e))
            return {
                "total_jobs": 0,
                "jobs_by_status": {},
                "avg_processing_time": 0.0,
                "recent_jobs_24h": 0
            }


# Create global database manager instance
db_manager = DatabaseManager()
