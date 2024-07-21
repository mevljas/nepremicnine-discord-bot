import threading

# Lock for accessing  domain_available_times and ip_available_times by multiple threads.
lock = threading.Lock()
