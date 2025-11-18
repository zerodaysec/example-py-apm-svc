#!/usr/bin/env python3
"""
Task Runner for Celery APM Demo
Sends various tasks to the Celery worker for testing APM instrumentation
"""
import time
from celery_worker_apm import (
    send_email,
    process_image,
    generate_report,
    data_sync,
    complex_workflow,
    failing_task
)


def run_all_tasks():
    """Execute all demo tasks"""
    print("\n" + "="*60)
    print("Celery APM Demo - Task Runner")
    print("="*60 + "\n")

    tasks_results = []

    # Task 1: Send Email
    print("1. Queuing email task...")
    email_result = send_email.delay(
        recipient='user@example.com',
        subject='APM Test Email',
        body='This is a test email for APM monitoring'
    )
    tasks_results.append(('Send Email', email_result))
    print(f"   Task ID: {email_result.id}")

    # Task 2: Process Image
    print("\n2. Queuing image processing task...")
    image_result = process_image.delay(
        image_url='https://example.com/image.jpg',
        transformations=['resize', 'crop', 'filter', 'compress']
    )
    tasks_results.append(('Process Image', image_result))
    print(f"   Task ID: {image_result.id}")

    # Task 3: Generate Report
    print("\n3. Queuing report generation task...")
    report_result = generate_report.delay(
        report_type='monthly_sales',
        date_range={'start': '2024-01-01', 'end': '2024-01-31'}
    )
    tasks_results.append(('Generate Report', report_result))
    print(f"   Task ID: {report_result.id}")

    # Task 4: Data Sync
    print("\n4. Queuing data sync task...")
    sync_result = data_sync.delay(
        source='postgres://source_db',
        destination='postgres://dest_db',
        batch_size=100
    )
    tasks_results.append(('Data Sync', sync_result))
    print(f"   Task ID: {sync_result.id}")

    # Task 5: Complex Workflow
    print("\n5. Queuing complex workflow task...")
    workflow_result = complex_workflow.delay(
        workflow_id=f'workflow_{int(time.time())}'
    )
    tasks_results.append(('Complex Workflow', workflow_result))
    print(f"   Task ID: {workflow_result.id}")

    # Task 6: Failing Task (50% chance of failure)
    print("\n6. Queuing failing task (50% failure rate)...")
    failing_result = failing_task.delay(fail_probability=0.5)
    tasks_results.append(('Failing Task', failing_result))
    print(f"   Task ID: {failing_result.id}")

    print("\n" + "="*60)
    print("All tasks queued successfully!")
    print("="*60 + "\n")

    # Wait for all tasks to complete
    print("Waiting for tasks to complete...\n")
    for task_name, result in tasks_results:
        try:
            print(f"Waiting for '{task_name}'...")
            output = result.get(timeout=30)
            print(f"  ✓ {task_name} completed: {output}")
        except Exception as e:
            print(f"  ✗ {task_name} failed: {e}")

    print("\n" + "="*60)
    print("Task execution completed!")
    print("Check your APM dashboard for detailed metrics")
    print("="*60 + "\n")


def run_specific_task(task_name: str):
    """Run a specific task by name"""
    task_map = {
        'email': lambda: send_email.delay('test@example.com', 'Test', 'Body'),
        'image': lambda: process_image.delay('https://example.com/img.jpg', ['resize']),
        'report': lambda: generate_report.delay('sales', {'start': '2024-01-01', 'end': '2024-01-31'}),
        'sync': lambda: data_sync.delay('source', 'dest', 50),
        'workflow': lambda: complex_workflow.delay(f'wf_{int(time.time())}'),
        'fail': lambda: failing_task.delay(0.5),
    }

    if task_name not in task_map:
        print(f"Unknown task: {task_name}")
        print(f"Available tasks: {', '.join(task_map.keys())}")
        return

    print(f"Queuing {task_name} task...")
    result = task_map[task_name]()
    print(f"Task ID: {result.id}")
    print("Waiting for result...")

    try:
        output = result.get(timeout=30)
        print(f"Result: {output}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        # Run specific task
        task_name = sys.argv[1]
        run_specific_task(task_name)
    else:
        # Run all tasks
        run_all_tasks()
