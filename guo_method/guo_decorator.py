import time

def timer(func):
    def wrapper(*args, **kwargs):
        # start the timer
        start_time = time.time()
        # call the decorated function
        result = func(*args, **kwargs)
        # remeasure the time
        end_time = time.time()
        # compute the elapsed time and print it
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
        # return the result of the decorated function execution
        return result
    # return reference to the wrapper function
    return wrapper

def debug(func):
    def wrapper(*args, **kwargs):
        # print the fucntion name and arguments
        print(f"Calling {func.__name__} with args: {args} kwargs: {kwargs}")
        # call the function
        result = func(*args, **kwargs)
        # print the results
        print(f"{func.__name__} returned: {result}")
        return result
    return wrapper
# @debug
# def add_numbers(x, y):
#     return x + y
# add_numbers(7, y=5,)  # Output: Calling add_numbers with args: (7) kwargs: {'y': 5} \n add_numbers returned: 12

def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Handle the exception
            print(f"An exception occurred: {str(e)}")
            # Optionally, perform additional error handling or logging
            # Reraise the exception if needed
    return wrapper
# @exception_handler
# def divide(x, y):
#     result = x / y
#     return result
# divide(10, 0)  # Output: An exception occurred: division by zero
def validate_input(*validations):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i, val in enumerate(args):
                if i < len(validations):
                    if not validations[i](val):
                        raise ValueError(f"Invalid argument: {val}")
            for key, val in kwargs.items():
                if key in validations[len(args):]:
                    if not validations[len(args):][key](val):
                        raise ValueError(f"Invalid argument: {key}={val}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
# @validate_input(lambda x: x > 0, lambda y: isinstance(y, str))
# def divide_and_print(x, message):
#     print(message)
#     return 1 / x

# divide_and_print(5, "Hello!")  # Output: Hello! 1.0


def retry(max_attempts, delay=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    print(f"Attempt {attempts} failed: {e}")
                    time.sleep(delay)
            print(f"Function failed after {max_attempts} attempts")
        return wrapper
    return decorator
# @retry(max_attempts=3, delay=2)
# def fetch_data(url):
#     print("Fetching the data..")
#     # raise timeout error to simulate a server not responding..
#     raise TimeoutError("Server is not responding.")
# fetch_data("https://example.com/data")  # Retries 3 times with