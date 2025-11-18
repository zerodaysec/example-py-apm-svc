"""
Celery Worker with APM Instrumentation
Demonstrates APM tracking for background tasks and distributed work queues
"""
import os
import time
import random
from celery import Celery, Task
from celery.signals import task_prerun, task_postrun, task_failure
import elasticapm
from elasticapm.contrib.celery import register_exception_tracking, register_instrumentation
from dotenv import load_dotenv

load_dotenv()

# Configure Celery
app = Celery(
    'apm_tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

# Initialize APM client
apm_client = elasticapm.Client(
    service_name=os.getenv('ELASTIC_APM_SERVICE_NAME', 'celery-worker-apm-demo'),
    server_url=os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
    secret_token=os.getenv('ELASTIC_APM_SECRET_TOKEN', ''),
    environment=os.getenv('ENVIRONMENT', 'development'),
    debug=os.getenv('ELASTIC_APM_DEBUG', 'true').lower() == 'true',
)

# Register APM instrumentation for Celery
register_exception_tracking(apm_client)
register_instrumentation(apm_client)
elasticapm.instrument()


class APMTask(Task):
    """Custom Task class that adds APM transaction tracking"""

    def __call__(self, *args, **kwargs):
        """Wrap task execution in APM transaction"""
        transaction = apm_client.begin_transaction('celery-task')
        elasticapm.set_transaction_name(f'task.{self.name}')

        elasticapm.label(
            task_name=self.name,
            task_id=self.request.id if self.request else 'unknown'
        )

        try:
            result = super().__call__(*args, **kwargs)
            elasticapm.set_transaction_result('success')
            return result
        except Exception as e:
            elasticapm.capture_exception()
            elasticapm.set_transaction_result('failure')
            raise
        finally:
            apm_client.end_transaction(self.name)


# Set default task base class
app.Task = APMTask


@app.task(bind=True, name='tasks.send_email')
def send_email(self, recipient: str, subject: str, body: str):
    """Simulates sending an email with APM tracking"""
    with elasticapm.capture_span('email_preparation', 'email'):
        time.sleep(0.2)
        elasticapm.label(recipient=recipient, subject=subject)
        print(f"Preparing email to {recipient}: {subject}")

    with elasticapm.capture_span('email_sending', 'email.smtp'):
        # Simulate SMTP operation
        time.sleep(random.uniform(0.5, 1.5))
        success = random.random() > 0.1  # 90% success rate

        if not success:
            raise Exception("Failed to send email - SMTP connection error")

        elasticapm.label(sent=True, delivery_time_ms=int(random.uniform(500, 1500)))
        print(f"Email sent successfully to {recipient}")

    return {'status': 'sent', 'recipient': recipient}


@app.task(bind=True, name='tasks.process_image')
def process_image(self, image_url: str, transformations: list):
    """Simulates image processing with APM tracking"""
    with elasticapm.capture_span('download_image', 'http'):
        time.sleep(0.5)
        elasticapm.label(url=image_url, size_mb=random.uniform(1, 10))
        print(f"Downloaded image from {image_url}")

    results = []
    for transform in transformations:
        with elasticapm.capture_span(f'transform_{transform}', 'processing.image'):
            time.sleep(random.uniform(0.3, 0.8))
            elasticapm.label(transformation=transform, applied=True)
            results.append({'transformation': transform, 'status': 'completed'})
            print(f"Applied transformation: {transform}")

    with elasticapm.capture_span('upload_result', 'http'):
        time.sleep(0.3)
        result_url = f"https://cdn.example.com/processed/{random.randint(1000, 9999)}.jpg"
        elasticapm.label(result_url=result_url)
        print(f"Uploaded processed image to {result_url}")

    return {
        'status': 'completed',
        'transformations': results,
        'result_url': result_url
    }


@app.task(bind=True, name='tasks.generate_report')
def generate_report(self, report_type: str, date_range: dict):
    """Simulates report generation with APM tracking"""
    with elasticapm.capture_span('fetch_data', 'db.query'):
        time.sleep(0.8)
        record_count = random.randint(100, 10000)
        elasticapm.label(report_type=report_type, records=record_count)
        print(f"Fetched {record_count} records for {report_type} report")

    with elasticapm.capture_span('calculate_metrics', 'processing'):
        time.sleep(1.0)
        metrics = {
            'total': record_count,
            'average': random.uniform(50, 500),
            'max': random.uniform(500, 1000),
            'min': random.uniform(10, 50)
        }
        elasticapm.label(metrics_calculated=len(metrics))
        print(f"Calculated metrics: {metrics}")

    with elasticapm.capture_span('generate_pdf', 'file.generation'):
        time.sleep(1.2)
        filename = f"report_{report_type}_{int(time.time())}.pdf"
        elasticapm.label(filename=filename, pages=random.randint(5, 50))
        print(f"Generated report: {filename}")

    return {
        'status': 'completed',
        'report_type': report_type,
        'filename': filename,
        'metrics': metrics
    }


@app.task(bind=True, name='tasks.data_sync')
def data_sync(self, source: str, destination: str, batch_size: int = 100):
    """Simulates data synchronization with APM tracking"""
    total_records = random.randint(500, 2000)
    batches = (total_records // batch_size) + 1

    elasticapm.label(
        source=source,
        destination=destination,
        total_records=total_records,
        batch_size=batch_size
    )

    synced_records = 0

    for batch_num in range(batches):
        with elasticapm.capture_span(f'sync_batch_{batch_num}', 'db.sync'):
            records_in_batch = min(batch_size, total_records - synced_records)

            # Simulate data extraction
            with elasticapm.capture_span('extract', 'db.read'):
                time.sleep(random.uniform(0.1, 0.3))

            # Simulate data transformation
            with elasticapm.capture_span('transform', 'processing'):
                time.sleep(random.uniform(0.05, 0.15))

            # Simulate data loading
            with elasticapm.capture_span('load', 'db.write'):
                time.sleep(random.uniform(0.1, 0.3))

            synced_records += records_in_batch
            elasticapm.label(
                batch=batch_num,
                records_synced=records_in_batch
            )
            print(f"Synced batch {batch_num + 1}/{batches}: {records_in_batch} records")

    return {
        'status': 'completed',
        'total_records': synced_records,
        'batches': batches
    }


@app.task(bind=True, name='tasks.complex_workflow')
def complex_workflow(self, workflow_id: str):
    """Demonstrates a complex workflow with multiple sub-tasks"""
    elasticapm.set_custom_context({
        'workflow_id': workflow_id,
        'workflow_type': 'complex_multi_step'
    })

    # Step 1: Data validation
    with elasticapm.capture_span('step_1_validation', 'validation'):
        time.sleep(0.5)
        elasticapm.label(step=1, validation_passed=True)
        print("Step 1: Validation completed")

    # Step 2: Data enrichment
    with elasticapm.capture_span('step_2_enrichment', 'processing'):
        time.sleep(0.8)
        enriched_fields = random.randint(5, 15)
        elasticapm.label(step=2, enriched_fields=enriched_fields)
        print(f"Step 2: Enriched {enriched_fields} fields")

    # Step 3: External API calls
    with elasticapm.capture_span('step_3_api_calls', 'external'):
        for i in range(3):
            with elasticapm.capture_span(f'api_call_{i}', 'external.http'):
                time.sleep(random.uniform(0.2, 0.5))
                elasticapm.label(api_endpoint=f'endpoint_{i}', status=200)
        print("Step 3: External API calls completed")

    # Step 4: Data persistence
    with elasticapm.capture_span('step_4_persistence', 'db.write'):
        time.sleep(0.6)
        elasticapm.label(step=4, records_saved=random.randint(10, 100))
        print("Step 4: Data persisted")

    # Step 5: Notification
    with elasticapm.capture_span('step_5_notification', 'notification'):
        time.sleep(0.3)
        elasticapm.label(step=5, notification_sent=True)
        print("Step 5: Notification sent")

    return {
        'workflow_id': workflow_id,
        'status': 'completed',
        'steps_completed': 5
    }


@app.task(bind=True, name='tasks.failing_task')
def failing_task(self, fail_probability: float = 0.5):
    """Task that randomly fails to demonstrate error tracking"""
    with elasticapm.capture_span('risky_operation', 'custom'):
        time.sleep(0.5)

        if random.random() < fail_probability:
            elasticapm.label(expected_failure=True)
            raise ValueError(f"Task failed with probability {fail_probability}")

        elasticapm.label(success=True)
        return {'status': 'success'}


# Celery signals for additional APM tracking
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log task start"""
    print(f"Task {task.name} [{task_id}] starting...")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None,
                         retval=None, **extra):
    """Log task completion"""
    print(f"Task {task.name} [{task_id}] completed successfully")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None,
                        kwargs=None, traceback=None, einfo=None, **extra):
    """Log task failure"""
    print(f"Task {sender.name} [{task_id}] failed: {exception}")


if __name__ == '__main__':
    print("="*60)
    print("Celery Worker APM Demo")
    print(f"Broker: {app.conf.broker_url}")
    print(f"APM Service: {apm_client.config.service_name}")
    print(f"APM Server: {apm_client.config.server_url}")
    print("="*60)
    print("\nTo start the worker, run:")
    print("  celery -A celery_worker_apm worker --loglevel=info")
    print("\nTo test tasks, run the task_runner.py script")
    print("="*60)
