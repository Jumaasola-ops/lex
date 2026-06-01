"""
Multi-Device Batch Processing with Orchestration.
Author: Asola Junior
Processes multiple Android devices in parallel with load balancing and retry logic.
"""

import concurrent.futures
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from adb_manager import ADBManager
from utils import log_info, log_error, log_warning


class TaskStatus(Enum):
    """Status of a batch task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    """Result of a single device task."""
    device_id: str
    task_name: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str = ""
    duration_seconds: float = 0.0
    retry_count: int = 0
    
    def finalize(self, status: TaskStatus, result: Any = None, error: str = None):
        """Finalize task result."""
        self.status = status
        self.result = result
        self.error = error
        self.end_time = datetime.now().isoformat()
        self.duration_seconds = (
            datetime.fromisoformat(self.end_time) - 
            datetime.fromisoformat(self.start_time)
        ).total_seconds()


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    max_workers: int = 4  # Number of parallel workers
    max_retries: int = 3  # Max retries per device
    retry_delay_seconds: float = 5.0  # Delay between retries
    timeout_seconds: float = 300.0  # Timeout per task
    stop_on_error: bool = False  # Stop batch on first error
    verbose: bool = True  # Verbose logging


class DeviceBatchProcessor:
    """Orchestrates batch operations across multiple devices."""
    
    def __init__(self, config: BatchConfig = None):
        """
        Initialize batch processor.
        
        Args:
            config: Batch configuration
        """
        self.config = config or BatchConfig()
        self.adb = ADBManager()
        self.results: List[TaskResult] = []
        self.active_devices: Dict[str, bool] = {}
    
    def discover_devices(self) -> List[str]:
        """
        Discover all connected devices.
        
        Returns:
            List[str]: List of device IDs
        """
        devices = self.adb.list_devices()
        log_info(f"Discovered {len(devices)} device(s)")
        return devices
    
    def process_batch(
        self,
        task_func: Callable,
        device_ids: List[str],
        task_name: str = "batch_task",
        **task_kwargs
    ) -> Dict[str, TaskResult]:
        """
        Process task across multiple devices in parallel.
        
        Args:
            task_func: Function to execute on each device
            device_ids: List of device IDs to process
            task_name: Name of the task
            **task_kwargs: Additional arguments for task function
            
        Returns:
            Dict[str, TaskResult]: Results by device ID
        """
        self.results = []
        start_time = time.time()
        
        log_info(f"Starting batch task '{task_name}' on {len(device_ids)} device(s)")
        log_info(f"Workers: {self.config.max_workers}, Max retries: {self.config.max_retries}")
        
        # Initialize device tracking
        self.active_devices = {device_id: True for device_id in device_ids}
        
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.max_workers
        ) as executor:
            futures = {}
            
            # Submit initial tasks
            for device_id in device_ids:
                future = executor.submit(
                    self._execute_task_with_retry,
                    task_func,
                    device_id,
                    task_name,
                    **task_kwargs
                )
                futures[future] = device_id
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                device_id = futures[future]
                try:
                    result = future.result(timeout=self.config.timeout_seconds)
                    self.results.append(result)
                    
                    if self.config.verbose:
                        status_icon = "✓" if result.status == TaskStatus.COMPLETED else "✗"
                        log_info(f"{status_icon} {device_id}: {result.status.value}")
                    
                    if self.config.stop_on_error and result.status == TaskStatus.FAILED:
                        executor.shutdown(wait=False)
                        break
                
                except concurrent.futures.TimeoutError:
                    result = TaskResult(
                        device_id=device_id,
                        task_name=task_name,
                        status=TaskStatus.FAILED,
                        error=f"Task timeout after {self.config.timeout_seconds}s"
                    )
                    result.finalize(TaskStatus.FAILED, error=result.error)
                    self.results.append(result)
                    log_error(f"Task timeout on {device_id}")
                
                except Exception as e:
                    result = TaskResult(
                        device_id=device_id,
                        task_name=task_name,
                        status=TaskStatus.FAILED,
                        error=str(e)
                    )
                    result.finalize(TaskStatus.FAILED, error=str(e))
                    self.results.append(result)
                    log_error(f"Task error on {device_id}: {e}")
        
        # Calculate batch statistics
        elapsed = time.time() - start_time
        self._log_batch_summary(elapsed)
        
        return {r.device_id: r for r in self.results}
    
    def _execute_task_with_retry(
        self,
        task_func: Callable,
        device_id: str,
        task_name: str,
        **task_kwargs
    ) -> TaskResult:
        """
        Execute task with retry logic.
        
        Args:
            task_func: Function to execute
            device_id: Device ID
            task_name: Task name
            **task_kwargs: Task arguments
            
        Returns:
            TaskResult: Result of execution
        """
        result = TaskResult(
            device_id=device_id,
            task_name=task_name,
            status=TaskStatus.PENDING,
        )
        
        # Check device availability
        if not self._is_device_available(device_id):
            result.finalize(
                TaskStatus.SKIPPED,
                error=f"Device {device_id} not available"
            )
            log_warning(f"Skipping {device_id}: device not available")
            return result
        
        # Retry loop
        for attempt in range(self.config.max_retries):
            try:
                result.status = TaskStatus.RUNNING if attempt == 0 else TaskStatus.RETRYING
                result.retry_count = attempt
                
                if attempt > 0:
                    log_warning(f"Retrying {device_id} (attempt {attempt + 1}/{self.config.max_retries})")
                    time.sleep(self.config.retry_delay_seconds)
                
                # Execute task
                task_result = task_func(device_id, **task_kwargs)
                
                result.finalize(TaskStatus.COMPLETED, result=task_result)
                return result
            
            except Exception as e:
                error_msg = str(e)
                
                # Determine if error is retryable
                if not self._is_retryable_error(error_msg) or attempt == self.config.max_retries - 1:
                    result.finalize(TaskStatus.FAILED, error=error_msg)
                    return result
        
        return result
    
    def _is_device_available(self, device_id: str) -> bool:
        """Check if device is connected and available."""
        try:
            output = self.adb.execute_command(device_id, "getprop ro.build.version.sdk")
            return bool(output)
        except:
            return False
    
    def _is_retryable_error(self, error_msg: str) -> bool:
        """
        Determine if error is retryable.
        
        Args:
            error_msg: Error message
            
        Returns:
            bool: True if retryable
        """
        non_retryable = [
            "device not found",
            "offline",
            "validation failed",
            "permission denied",
        ]
        
        error_lower = error_msg.lower()
        return not any(err in error_lower for err in non_retryable)
    
    def _log_batch_summary(self, elapsed: float):
        """Log batch execution summary."""
        completed = sum(1 for r in self.results if r.status == TaskStatus.COMPLETED)
        failed = sum(1 for r in self.results if r.status == TaskStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TaskStatus.SKIPPED)
        
        log_info("=" * 50)
        log_info(f"Batch Summary ({elapsed:.1f}s):")
        log_info(f"  Total devices: {len(self.results)}")
        log_info(f"  Completed: {completed}")
        log_info(f"  Failed: {failed}")
        log_info(f"  Skipped: {skipped}")
        log_info("=" * 50)
    
    def get_results_by_status(self, status: TaskStatus) -> List[TaskResult]:
        """
        Get results filtered by status.
        
        Args:
            status: Task status to filter by
            
        Returns:
            List[TaskResult]: Filtered results
        """
        return [r for r in self.results if r.status == status]
    
    def get_failed_devices(self) -> List[str]:
        """Get list of failed devices."""
        return [r.device_id for r in self.get_results_by_status(TaskStatus.FAILED)]
    
    def retry_failed_devices(
        self,
        task_func: Callable,
        task_name: str = "retry_task",
        **task_kwargs
    ) -> Dict[str, TaskResult]:
        """
        Retry failed devices.
        
        Args:
            task_func: Function to execute
            task_name: Task name
            **task_kwargs: Task arguments
            
        Returns:
            Dict[str, TaskResult]: New results
        """
        failed = self.get_failed_devices()
        
        if not failed:
            log_info("No failed devices to retry")
            return {}
        
        log_info(f"Retrying {len(failed)} failed device(s)...")
        
        # Temporarily increase retry count
        original_retries = self.config.max_retries
        self.config.max_retries = 2
        
        new_results = self.process_batch(task_func, failed, task_name, **task_kwargs)
        
        self.config.max_retries = original_retries
        
        return new_results
    
    def get_aggregated_results(self) -> Dict[str, Any]:
        """
        Get aggregated batch results.
        
        Returns:
            Dict with aggregated statistics and data
        """
        total_time = sum(r.duration_seconds for r in self.results)
        avg_time = total_time / len(self.results) if self.results else 0
        
        return {
            "summary": {
                "total_devices": len(self.results),
                "completed": sum(1 for r in self.results if r.status == TaskStatus.COMPLETED),
                "failed": sum(1 for r in self.results if r.status == TaskStatus.FAILED),
                "skipped": sum(1 for r in self.results if r.status == TaskStatus.SKIPPED),
            },
            "timing": {
                "total_seconds": total_time,
                "average_seconds": avg_time,
            },
            "devices": {r.device_id: r for r in self.results},
            "failed_devices": self.get_failed_devices(),
        }


class BatchTaskTemplate:
    """Template for common batch operations."""
    
    @staticmethod
    def scan_malware(device_id: str, scanner) -> Dict[str, Any]:
        """
        Scan device for malware.
        
        Args:
            device_id: Device ID
            scanner: MalwareScanner instance
            
        Returns:
            Dict with scan results
        """
        return scanner.scan_device(device_id)
    
    @staticmethod
    def collect_device_info(device_id: str, adb: ADBManager) -> Dict[str, str]:
        """
        Collect device information.
        
        Args:
            device_id: Device ID
            adb: ADBManager instance
            
        Returns:
            Dict with device info
        """
        return {
            "device_id": device_id,
            "model": adb.execute_command(device_id, "getprop ro.product.model").strip(),
            "android_version": adb.execute_command(device_id, "getprop ro.build.version.release").strip(),
            "api_level": adb.execute_command(device_id, "getprop ro.build.version.sdk").strip(),
        }
    
    @staticmethod
    def analyze_apps(device_id: str, analyzer) -> Dict[str, Any]:
        """
        Analyze apps on device.
        
        Args:
            device_id: Device ID
            analyzer: AppAnalyzer instance
            
        Returns:
            Dict with analysis results
        """
        return analyzer.analyze_device(device_id)


def main():
    """Test batch processor."""
    config = BatchConfig(max_workers=2, max_retries=2)
    processor = DeviceBatchProcessor(config)
    
    # Discover devices
    devices = processor.discover_devices()
    
    if not devices:
        print("No devices found")
        return
    
    print(f"\nBatch processing ready for {len(devices)} device(s)")
    print("Available devices:", devices)
    print("\nUse processor.process_batch(task_func, devices, 'task_name') to start")


if __name__ == "__main__":
    main()
