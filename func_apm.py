import time
import elasticapm

elasticapm.instrument()

def function_one():
    with elasticapm.capture_span("Function One"):
        # Your code for function one
        time.sleep(1)

def function_two():
    with elasticapm.capture_span("Function Two"):
        # Your code for function two
        time.sleep(2)

if __name__ == "__main__":
    elasticapm.start(
        service_name="Your Service Name",
        server_url="http://your-apm-server:8200",
        secret_token="Your Secret Token",
        debug=True  # Set to False in production
    )

    function_one()
    function_two()

    elasticapm.stop()
