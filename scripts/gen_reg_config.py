"""One-off: generate HTTP config with proxy registration (mcp_proxy_adapter SimpleConfigGenerator)."""

from mcp_proxy_adapter.core.config.simple_config_generator import SimpleConfigGenerator


def main() -> None:
    path = SimpleConfigGenerator().generate(
        "http",
        with_proxy=True,
        out_path="config/http_reg.json",
        server_host="127.0.0.1",
        server_port=20003,
        registration_host="127.0.0.1",
        registration_port=3005,
        registration_protocol="http",
        registration_server_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        registration_server_name="vast_srv",
    )
    print(path)


if __name__ == "__main__":
    main()
