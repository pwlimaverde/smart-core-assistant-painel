import ssl
import socket
import os
import sys


def check_ssl():
    print("--- SSL Context Info ---")
    print(f"Default verify paths: {ssl.get_default_verify_paths()}")

    ctx = ssl.create_default_context()
    print(f"Cert store stats: {ctx.cert_store_stats()}")

    print("\n--- Environment Variables ---")
    print(f"SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE')}")
    print(f"SSL_CERT_DIR: {os.environ.get('SSL_CERT_DIR')}")

    print("\n--- Connection Test (smtp-relay.brevo.com:587) ---")
    try:
        sock = socket.create_connection(
            ("smtp-relay.brevo.com", 587), timeout=10
        )
        # SMTP usually starts plain text then upgrades with STARTTLS, but we can try wrapping to see if it verifies
        # However, port 587 is usually STARTTLS.
        # For simple verification of CA store, we can try to connect to an HTTPS site or just check the store.
        # Let's try connecting to google.com:443 as a sanity check for general SSL outbound.
        print(
            "Connected to TCP port 587. (Testing HTTPS handshake on google.com for cert verification...)"
        )

        with socket.create_connection(("www.google.com", 443)) as tcp_sock:
            with ctx.wrap_socket(
                tcp_sock, server_hostname="www.google.com"
            ) as tls_sock:
                print(
                    f"HTTPS Connection to www.google.com successful. Cipher: {tls_sock.cipher()}"
                )
                print("SSL Certificate verification works for standard sites.")

    except Exception as e:
        print(f"Connection/SSL Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    check_ssl()
