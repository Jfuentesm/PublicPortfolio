import time
import logging
import sqlalchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

from core.logging_config import get_logger, set_log_context, LogTimer, get_correlation_id

logger = get_logger("vendor_classification.database")

class SQLQueryLoggingMiddleware:
    """Middleware for logging SQL queries."""
    
    def __init__(self, engine):
        """Initialize the middleware with an SQLAlchemy engine."""
        self.engine = engine
        self.register_events()
        logger.info("SQL query logging middleware initialized")
    
    def register_events(self):
        """Register SQLAlchemy event listeners."""
        event.listen(self.engine, "before_cursor_execute", self.before_cursor_execute)
        event.listen(self.engine, "after_cursor_execute", self.after_cursor_execute)
        event.listen(self.engine, "handle_error", self.handle_error)
        logger.debug("SQLAlchemy event listeners registered")
    
    def before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Log query before execution and store start time."""
        conn.info.setdefault('query_start_time', []).append(time.time())
        
        # Truncate long queries for readability
        statement_str = str(statement)
        if len(statement_str) > 1000:
            statement_str = statement_str[:997] + "..."
        
        # Format parameters safely for logging
        params_str = str(parameters)
        if len(params_str) > 500:
            params_str = params_str[:497] + "..."
        
        logger.debug(
            f"Executing SQL query", 
            extra={
                "statement": statement_str,
                "parameters": params_str,
                "executemany": executemany,
                "connection_id": id(conn),
                "correlation_id": get_correlation_id()
            }
        )
    
    def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Log query completion and execution time."""
        if not conn.info.get('query_start_time'):
            return
        
        start_time = conn.info['query_start_time'].pop(-1)
        total_time = time.time() - start_time
        
        # Get result details safely
        row_count = -1
        try:
            row_count = cursor.rowcount
        except:
            pass
        
        # Store query timing in thread-local storage for stats
        statement_type = statement.split(' ')[0].upper() if isinstance(statement, str) else "UNKNOWN"
        
        logger.debug(
            f"SQL query completed", 
            extra={
                "duration": total_time,
                "row_count": row_count,
                "statement_type": statement_type,
                "connection_id": id(conn),
                "correlation_id": get_correlation_id()
            }
        )
        
        # Add to performance stats
        set_log_context({f"db_{statement_type.lower()}_count": 1})
        set_log_context({f"db_{statement_type.lower()}_time": total_time})
    
    def handle_error(self, context):
        """Log database errors."""
        logger.error(
            f"Database error occurred", 
            exc_info=context.original_exception,
            extra={
                "statement": str(context.statement) if context.statement else None,
                "parameters": str(context.parameters) if context.parameters else None,
                "correlation_id": get_correlation_id()
            }
        )

def setup_db_logging(engine=None):
    """Set up database query logging."""
    if engine is None:
        # Get all engines if specific one not provided
        for instance in Engine.__subclasses__():
            for engine in instance.instances:
                SQLQueryLoggingMiddleware(engine)
    else:
        SQLQueryLoggingMiddleware(engine)
    
    logger.info("Database query logging initialized")