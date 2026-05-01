#!/usr/bin/env python3
"""Demo script for SSL test environment.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.ssl_test_environment import SSLTestEnvironment  # noqa: E402


def demo_ssl_test_environment() -> None:
    """Demonstrate SSL test environment functionality."""
    print("🚀 SSL Test Environment Demo")
    print("=" * 50)

    # Create test environment
    with SSLTestEnvironment(cleanup_on_exit=True) as env:
        print(f"✅ Environment created at: {env.get_base_directory()}")

        # Setup environment
        env.setup_environment()
        print("✅ Environment setup completed")

        # Generate test configurations
        configs = env.generate_test_configs(
            server_host="127.0.0.1",
            server_port=20000,
            ssl_enabled=True,
            security_enabled=True,
        )
        print(f"✅ Generated {len(configs)} configuration files:")
        for config_type, config_path in configs.items():
            print(f"   - {config_type}: {config_path}")

        # Create test data
        test_data = env.create_test_data()
        print(f"✅ Created {len(test_data)} test data files:")
        for data_type, data_path in test_data.items():
            print(f"   - {data_type}: {data_path}")

        # Validate environment
        validation_results = env.validate_environment()
        print("✅ Environment validation results:")
        for component, is_valid in validation_results.items():
            status = "✅" if is_valid else "❌"
            print(f"   - {component}: {status}")

        print("\n📊 Environment status:")
        print(f"   - Setup: {'✅' if env.is_setup() else '❌'}")
        print(f"   - Validated: {'✅' if env.is_validated() else '❌'}")
        print(f"   - Configurations: {len(env.configs)}")
        print(f"   - Test data files: {len(test_data)}")

    print("\n🎉 Demo completed successfully!")
    print("Environment was automatically cleaned up.")


if __name__ == "__main__":
    demo_ssl_test_environment()
