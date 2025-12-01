#!/usr/bin/env python3
"""
Generate a QR code for easy mobile access to the Golf Calculator.
Scan the QR code with your iPhone camera to instantly open the app.
"""

import sys
import socket

def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return None

def generate_qr_ascii(url):
    """Generate an ASCII art QR code."""
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        return True
    except ImportError:
        return False

def main():
    local_ip = get_local_ip()
    
    if not local_ip:
        print("❌ Could not determine local IP address")
        sys.exit(1)
    
    url = f"http://{local_ip}:8000"
    
    print("\n" + "="*50)
    print("📱 Golf Calculator - iPhone Quick Connect")
    print("="*50 + "\n")
    print(f"🌐 URL: {url}\n")
    
    # Try to generate QR code
    if generate_qr_ascii(url):
        print("\n📷 Scan this QR code with your iPhone camera:")
        print("   (Your iPhone will automatically detect and open it)\n")
    else:
        print("💡 Install qrcode for QR code generation:")
        print("   pip install qrcode[pil]\n")
        print("   Then run this script again to see a QR code!")
        print("\n📋 Or manually enter this URL in Safari:")
        print(f"   {url}\n")
    
    print("="*50)
    print("\n✓ Server should be running on port 8000")
    print("✓ Make sure iPhone is on same Wi-Fi network\n")

if __name__ == "__main__":
    main()
