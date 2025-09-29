# Centralized print-based logging functions
def console_info(message, module="Default"):
    print(f"ℹ️  [{module}] {message}")

def console_debug(message, module="Default"):
    print(f"🐛 [{module}] {message}")

def console_warning(message, module="Default"):
    print(f"⚠️  [{module}] {message}")

def console_error(message, module="Default"):
    print(f"❌ [{module}] {message}")

def console_telemetry_event(event_name, properties, module="Default"):
    print(f"📊 [{module}] {event_name}: {properties}")
