"""
Standalone function-based APM instrumentation example
Shows how to use APM in non-web applications like batch jobs, scripts, or background workers
"""
import os
import time
import random
import elasticapm
from elasticapm import capture_span, set_transaction_name, set_custom_context, label
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

load_dotenv()

# SQLAlchemy setup
Base = declarative_base()


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class SalesRecord(Base):
    __tablename__ = 'sales'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    sale_date = Column(DateTime, default=datetime.utcnow)


# Initialize database
engine = create_engine('sqlite:///batch_demo.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def initialize_sample_data():
    """Initialize database with sample data"""
    with capture_span('initialize_data', 'db.setup'):
        session = Session()

        # Clear existing data
        session.query(Product).delete()
        session.query(SalesRecord).delete()

        # Add sample products
        products = [
            Product(name='Laptop', price=999.99, category='Electronics'),
            Product(name='Mouse', price=29.99, category='Electronics'),
            Product(name='Keyboard', price=79.99, category='Electronics'),
            Product(name='Monitor', price=299.99, category='Electronics'),
            Product(name='Desk Chair', price=199.99, category='Furniture'),
        ]
        session.add_all(products)
        session.commit()

        # Add sample sales records
        for _ in range(20):
            sale = SalesRecord(
                product_id=random.randint(1, 5),
                quantity=random.randint(1, 10),
                total_amount=random.uniform(50, 1000)
            )
            session.add(sale)

        session.commit()
        session.close()

        label(products_added=len(products), sales_added=20)
        print(f"Initialized {len(products)} products and 20 sales records")


def fetch_products():
    """Fetch all products from database"""
    with capture_span('fetch_products', 'db.query'):
        session = Session()
        products = session.query(Product).all()
        session.close()

        label(products_fetched=len(products))
        print(f"Fetched {len(products)} products")
        return products


def calculate_total_sales():
    """Calculate total sales amount"""
    with capture_span('calculate_sales', 'db.query'):
        session = Session()

        # Complex query to demonstrate APM tracking
        total_sales = session.query(SalesRecord).count()
        total_amount = sum(sale.total_amount for sale in session.query(SalesRecord).all())

        session.close()

        label(total_sales=total_sales, total_amount=round(total_amount, 2))
        print(f"Total sales: {total_sales}, Total amount: ${total_amount:.2f}")

        return {'count': total_sales, 'amount': total_amount}


def process_data_batch(batch_size: int = 10):
    """Process data in batches"""
    with capture_span('process_batch', 'processing'):
        results = []
        for i in range(batch_size):
            with capture_span(f'process_item_{i}', 'processing.item'):
                # Simulate processing
                time.sleep(random.uniform(0.05, 0.15))
                results.append({
                    'item': i,
                    'status': 'processed',
                    'value': random.randint(1, 100)
                })

        label(batch_size=batch_size, items_processed=len(results))
        print(f"Processed batch of {batch_size} items")
        return results


def generate_report():
    """Generate a comprehensive report"""
    with capture_span('generate_report', 'reporting'):
        # Get products
        products = fetch_products()

        # Calculate sales
        sales_data = calculate_total_sales()

        # Process some analytics
        with capture_span('analytics_processing', 'custom'):
            time.sleep(0.5)
            analytics = {
                'avg_sale_amount': sales_data['amount'] / sales_data['count'] if sales_data['count'] > 0 else 0,
                'product_count': len(products),
                'timestamp': datetime.utcnow().isoformat()
            }

        # Generate final report
        report = {
            'total_products': len(products),
            'total_sales': sales_data['count'],
            'total_revenue': sales_data['amount'],
            'analytics': analytics,
            'generated_at': datetime.utcnow().isoformat()
        }

        label(report_generated=True, products=len(products))
        print(f"Report generated: {report}")
        return report


def simulate_error_handling():
    """Demonstrates error handling with APM"""
    with capture_span('error_handling_demo', 'custom'):
        try:
            with capture_span('risky_operation', 'custom'):
                label(operation='risky', expected_error=True)

                # Simulate a potential error
                if random.random() < 0.7:
                    raise ValueError("Simulated processing error")

                print("Operation succeeded without error")

        except ValueError as e:
            # Capture the exception in APM
            elasticapm.capture_exception()
            label(error_handled=True, error_type='ValueError')
            print(f"Handled error: {e}")


def complex_transaction():
    """Demonstrates a complex transaction with multiple spans"""
    set_transaction_name('complex_batch_job')

    # Set custom context for the transaction
    set_custom_context({
        'job_type': 'batch_processing',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'batch_id': f'batch_{int(time.time())}'
    })

    print("\n" + "="*60)
    print("Starting Complex Transaction")
    print("="*60)

    # Step 1: Initialize data
    with capture_span('step_1_initialization', 'setup'):
        initialize_sample_data()
        label(step=1, description='initialization')

    # Step 2: Fetch and process data
    with capture_span('step_2_data_processing', 'processing'):
        products = fetch_products()
        batch_results = process_data_batch(15)
        label(step=2, description='data_processing', items=len(batch_results))

    # Step 3: Calculate metrics
    with capture_span('step_3_metrics', 'analytics'):
        sales_data = calculate_total_sales()
        label(step=3, description='metrics')

    # Step 4: Generate report
    with capture_span('step_4_reporting', 'reporting'):
        report = generate_report()
        label(step=4, description='reporting')

    # Step 5: Error handling demonstration
    with capture_span('step_5_error_handling', 'custom'):
        simulate_error_handling()
        label(step=5, description='error_handling')

    print("="*60)
    print("Complex Transaction Completed")
    print("="*60 + "\n")


def main():
    """Main function to demonstrate APM in standalone scripts"""

    # Start APM client
    client = elasticapm.Client(
        service_name=os.getenv('ELASTIC_APM_SERVICE_NAME', 'batch-job-apm-demo'),
        server_url=os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
        secret_token=os.getenv('ELASTIC_APM_SECRET_TOKEN', ''),
        environment=os.getenv('ENVIRONMENT', 'development'),
        debug=os.getenv('ELASTIC_APM_DEBUG', 'true').lower() == 'true',
    )

    # Instrument libraries
    elasticapm.instrument()

    print("\n" + "="*60)
    print("APM Batch Job Demo - Starting")
    print(f"Service: {client.config.service_name}")
    print(f"Server: {client.config.server_url}")
    print("="*60 + "\n")

    # Begin transaction
    client.begin_transaction('batch_job')

    try:
        # Run complex transaction
        complex_transaction()

        # Mark transaction as successful
        elasticapm.set_transaction_result('success')

    except Exception as e:
        # Capture any unhandled exceptions
        elasticapm.capture_exception()
        elasticapm.set_transaction_result('failure')
        print(f"Transaction failed: {e}")

    finally:
        # End transaction
        client.end_transaction('batch_job')

        # Give APM time to send data
        time.sleep(1)

        # Close APM client
        client.close()

        print("\n" + "="*60)
        print("APM Batch Job Demo - Completed")
        print("="*60 + "\n")


if __name__ == "__main__":
    main()
