#!/bin/bash
# Fix permissions with correct group (domain users)

echo "=== Fixing Permissions with Correct Group ==="
echo "This ensures proper ownership with domain users group"
echo

# 1. Get current user and group
CURRENT_USER=$(whoami)
CURRENT_GROUP=$(id -gn)

echo "1. Current user details:"
echo "   User: $CURRENT_USER"
echo "   Primary group: $CURRENT_GROUP"
echo "   All groups: $(groups)"
echo

# 2. Detect the correct group
if groups | grep -q "domain users"; then
    CORRECT_GROUP="domain users"
elif groups | grep -q "Domain Users"; then
    CORRECT_GROUP="Domain Users"
else
    # Fallback to current primary group
    CORRECT_GROUP="$CURRENT_GROUP"
fi

echo "2. Using group: $CORRECT_GROUP"
echo

# 3. Check virtual environment
VENV="${VIRTUAL_ENV:-/moneyball/llama-env-py39}"
echo "3. Checking virtual environment: $VENV"

if [ ! -d "$VENV" ]; then
    echo "   ERROR: Virtual environment not found!"
    echo "   Please activate your environment first:"
    echo "   source /moneyball/llama-env-py39/bin/activate"
    exit 1
fi

# 4. Check current ownership
echo
echo "4. Current ownership of key directories:"

check_ownership() {
    local path=$1
    if [ -e "$path" ]; then
        local owner=$(stat -c '%U' "$path" 2>/dev/null)
        local group=$(stat -c '%G' "$path" 2>/dev/null)
        local perms=$(stat -c '%a' "$path" 2>/dev/null)
        echo "   $path"
        echo "     Owner: $owner, Group: $group, Perms: $perms"
        
        if [ "$owner" != "$CURRENT_USER" ] || [ "$group" != "$CORRECT_GROUP" ]; then
            echo "     ⚠️  Needs fixing!"
            return 1
        else
            echo "     ✓ Correct"
            return 0
        fi
    else
        echo "   $path - not found"
        return 2
    fi
}

NEEDS_FIX=0
check_ownership "$VENV" || NEEDS_FIX=1
check_ownership "$VENV/lib64/python3.9/site-packages" || NEEDS_FIX=1
check_ownership "$VENV/lib64/python3.9/site-packages/nvidia" || NEEDS_FIX=1
check_ownership "$VENV/lib64/python3.9/site-packages/torch" || NEEDS_FIX=1

# 5. Generate fix commands
if [ $NEEDS_FIX -eq 1 ]; then
    echo
    echo "5. PERMISSIONS NEED TO BE FIXED!"
    echo
    echo "   Run these commands to fix ownership:"
    echo
    echo "   # Fix entire virtual environment (recommended):"
    echo "   sudo chown -R $CURRENT_USER:\"$CORRECT_GROUP\" $VENV"
    echo
    echo "   # Or fix just site-packages:"
    echo "   sudo chown -R $CURRENT_USER:\"$CORRECT_GROUP\" $VENV/lib64/python3.9/site-packages"
    echo
    echo "   # After fixing, run this script again to verify"
    echo
    
    # Create a fix script
    cat > /tmp/fix_venv_permissions.sh << EOF
#!/bin/bash
# Auto-generated permission fix script
echo "Fixing permissions for $VENV..."
sudo chown -R $CURRENT_USER:"$CORRECT_GROUP" $VENV
echo "Done! Permissions fixed."
echo "Now run: ./fix_permissions_and_cuda.sh"
EOF
    chmod +x /tmp/fix_venv_permissions.sh
    
    echo "   Or run the generated script:"
    echo "   /tmp/fix_venv_permissions.sh"
    echo
    exit 0
else
    echo
    echo "5. ✅ All permissions are correct!"
fi

# 6. Additional checks for common permission issues
echo
echo "6. Checking for other permission issues..."

# Check if we can write to important directories
test_write_access() {
    local dir=$1
    local testfile="$dir/.permission_test_$$"
    
    if touch "$testfile" 2>/dev/null; then
        rm -f "$testfile"
        echo "   ✓ Write access to $dir"
        return 0
    else
        echo "   ✗ No write access to $dir"
        return 1
    fi
}

test_write_access "$VENV/bin"
test_write_access "$VENV/lib64/python3.9/site-packages"

# 7. Check for mixed ownership (common issue)
echo
echo "7. Checking for mixed ownership issues..."

find "$VENV/lib64/python3.9/site-packages" -type f ! -user "$CURRENT_USER" -o ! -group "$CORRECT_GROUP" 2>/dev/null | head -10 > /tmp/wrong_perms_$$

if [ -s /tmp/wrong_perms_$$ ]; then
    echo "   ⚠️  Found files with wrong ownership:"
    cat /tmp/wrong_perms_$$
    echo "   ..."
    echo
    echo "   Fix with:"
    echo "   sudo chown -R $CURRENT_USER:\"$CORRECT_GROUP\" $VENV/lib64/python3.9/site-packages"
else
    echo "   ✓ No mixed ownership issues found"
fi
rm -f /tmp/wrong_perms_$$

# 8. Summary
echo
echo "=== SUMMARY ==="
echo
echo "Correct ownership should be:"
echo "  User: $CURRENT_USER"
echo "  Group: $CORRECT_GROUP"
echo
echo "If you see any warnings above, fix with:"
echo "  sudo chown -R $CURRENT_USER:\"$CORRECT_GROUP\" $VENV"
echo
echo "After permissions are correct, run:"
echo "  ./fix_permissions_and_cuda.sh"
echo
echo "This will complete the CUDA 12 setup with proper permissions."

# 9. Create a permissions info file
cat > /moneyball/permissions_info.txt << EOF
Virtual Environment Permissions Info
Generated: $(date)

User: $CURRENT_USER
Group: $CORRECT_GROUP
Virtual Env: $VENV

Correct ownership command:
sudo chown -R $CURRENT_USER:"$CORRECT_GROUP" $VENV

Common issues:
1. Files created by root during pip install
2. Wrong group (should be "domain users" not just user name)
3. Mixed ownership from different install sessions
EOF

echo
echo "Permission info saved to: /moneyball/permissions_info.txt"