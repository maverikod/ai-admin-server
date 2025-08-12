#!/bin/bash

echo "=== Full FTP Debug ==="
echo ""

# 1. Проверяем систему
echo "1. System information:"
echo "   OS: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown')"
echo "   Kernel: $(uname -r)"
echo "   Architecture: $(uname -m)"
echo ""

# 2. Проверяем vsFTPd
echo "2. vsFTPd status:"
if command -v vsftpd >/dev/null 2>&1; then
    echo "   vsFTPd installed: $(vsftpd -version 2>&1 | head -1)"
    systemctl is-active vsftpd >/dev/null && echo "   ✓ vsFTPd is running" || echo "   ✗ vsFTPd is not running"
else
    echo "   ✗ vsFTPd not installed"
fi
echo ""

# 3. Проверяем конфигурацию
echo "3. vsFTPd configuration:"
if [ -f /etc/vsftpd.conf ]; then
    echo "   ✓ Config file exists"
    echo "   Key settings:"
    grep -E '(pasv|listen|local_enable|chroot)' /etc/vsftpd.conf | sed 's/^/     /'
else
    echo "   ✗ Config file missing"
fi
echo ""

# 4. Проверяем порты
echo "4. Port status:"
netstat -tlnp 2>/dev/null | grep -E '(21|20)' | sed 's/^/   /' || echo "   No FTP ports found"
echo ""

# 5. Проверяем файрвол
echo "5. Firewall status:"
echo "   iptables rules:"
iptables -L INPUT -n 2>/dev/null | grep -E '(21|20|RELATED|ESTABLISHED)' | sed 's/^/     /' || echo "     No FTP rules found"
echo ""

# 6. Проверяем модули
echo "6. Kernel modules:"
lsmod | grep -E '(ftp|conntrack)' | sed 's/^/   /' || echo "   No FTP modules loaded"
echo ""

# 7. Проверяем логи
echo "7. Recent logs:"
echo "   vsFTPd logs:"
tail -3 /var/log/vsftpd.log 2>/dev/null | sed 's/^/     /' || echo "     No vsFTPd logs"
echo "   System logs:"
journalctl -u vsftpd --no-pager -n 5 2>/dev/null | sed 's/^/     /' || echo "     No system logs"
echo ""

# 8. Тестируем без файрвола
echo "8. Testing without firewall:"
iptables -F 2>/dev/null
iptables -P INPUT ACCEPT 2>/dev/null
iptables -P FORWARD ACCEPT 2>/dev/null
iptables -P OUTPUT ACCEPT 2>/dev/null

timeout 10 bash -c "echo 'quit' | ftp localhost 21" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ FTP works without firewall"
else
    echo "   ✗ FTP doesn't work even without firewall"
    echo "   Problem is in vsFTPd configuration!"
fi
echo ""

# 9. Тестируем с минимальным файрволом
echo "9. Testing with minimal firewall:"
iptables -P INPUT DROP 2>/dev/null
iptables -A INPUT -i lo -j ACCEPT 2>/dev/null
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT 2>/dev/null
iptables -A INPUT -p tcp --dport 21 -j ACCEPT 2>/dev/null

timeout 10 bash -c "echo 'quit' | ftp localhost 21" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ FTP works with minimal firewall"
else
    echo "   ✗ FTP fails with minimal firewall"
    echo "   Adding passive ports..."
    iptables -A INPUT -p tcp --dport 1024:65535 -j ACCEPT 2>/dev/null
    
    timeout 10 bash -c "echo 'quit' | ftp localhost 21" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   ✓ FTP works with passive ports"
    else
        echo "   ✗ FTP still fails"
    fi
fi
echo ""

echo "=== Debug Complete ==="
echo ""
echo "Current firewall rules:"
iptables -L INPUT -n --line-numbers 2>/dev/null | head -10
echo ""
echo "Recommendations:"
echo "1. If FTP works without firewall: Use UFW instead of iptables"
echo "2. If FTP doesn't work: Check vsFTPd configuration"
echo "3. If vsFTPd not installed: apt-get install vsftpd" 