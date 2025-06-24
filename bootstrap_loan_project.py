#!/usr/bin/env python3
"""
BOOTSTRAP: Start fresh with loan analysis project
Sets up everything from scratch
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and show status"""
    print(f"\n📌 {description}")
    print(f"   Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            return True
        else:
            print(f"   ❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("LOAN PROJECT BOOTSTRAP")
    print("="*60)
    
    # 1. Check Python version
    print("\n1️⃣ Checking Python...")
    python_version = sys.version_info
    print(f"   Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major < 3 or python_version.minor < 8:
        print("   ⚠️  Python 3.8+ recommended")
    
    # 2. Clone or update repo
    print("\n2️⃣ Setting up GitHub repo...")
    if os.path.exists(".git"):
        run_command("git pull", "Updating existing repo")
    else:
        run_command(
            "git clone git@github.com:followthewhiterabbitneo/whisper-rtx-deployment.git .",
            "Cloning fresh repo"
        )
    
    # 3. Install dependencies
    print("\n3️⃣ Installing Python dependencies...")
    dependencies = [
        "pymysql",
        "requests",
        "fastapi",
        "uvicorn"
    ]
    
    for dep in dependencies:
        run_command(f"pip install {dep}", f"Installing {dep}")
    
    # 4. Test database connection
    print("\n4️⃣ Testing database connection...")
    test_code = """
import pymysql
try:
    conn = pymysql.connect(
        host='s40vpsoxweb002',
        port=3306,
        user='root',
        password='admin',
        database='oreka'
    )
    print('   ✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'   ❌ Database connection failed: {e}')
"""
    
    with open("test_db.py", "w") as f:
        f.write(test_code)
    
    run_command("python test_db.py", "Testing database")
    os.remove("test_db.py")
    
    # 5. Run initial data extraction
    print("\n5️⃣ Extracting loan data...")
    scripts_to_run = [
        ("get_all_loan_ids.py", "Extract all loan IDs"),
        ("count_all_loans.py", "Count loan statistics"),
        ("test_one_loan_simple.py", "Test with one loan")
    ]
    
    for script, desc in scripts_to_run:
        if os.path.exists(script):
            run_command(f"python {script}", desc)
        else:
            print(f"   ⚠️  {script} not found")
    
    # 6. Create project structure
    print("\n6️⃣ Creating project directories...")
    dirs_to_create = [
        "visualizations",
        "loan_reports", 
        "feedback_data",
        "exports"
    ]
    
    for dir_name in dirs_to_create:
        os.makedirs(dir_name, exist_ok=True)
        print(f"   📁 Created {dir_name}/")
    
    # 7. Summary
    print("\n" + "="*60)
    print("BOOTSTRAP COMPLETE!")
    print("="*60)
    
    print("\n🎯 Next steps:")
    print("   1. Run: python get_all_loan_ids.py")
    print("   2. Run: python smart_loan_network_finder.py")
    print("   3. Run: python visualize_loan_network.py")
    print("\n📊 Key scripts:")
    print("   - get_all_loan_ids.py          # Get all loans")
    print("   - smart_loan_network_finder.py # Find networks")
    print("   - visualize_loan_network.py    # Create visuals")
    print("   - loan_search_api.py           # Search API")
    
    print("\n🔗 Workflow:")
    print("   Loans → Networks → Visualizations → Clear to Close!")

if __name__ == "__main__":
    main()