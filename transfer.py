import pexpect
import sys

files_to_transfer = "main.py karung-dimuat-detection-di-feedmill-yolo26n-seg-200e.pt export_tensorrt.py"
host = "jetson@192.168.192.96"
dest = "~/keyy/"
password = "jetson"

command = f"scp -o StrictHostKeyChecking=no {files_to_transfer} {host}:{dest}"
print(f"Running: {command}")

child = pexpect.spawn(command, encoding='utf-8')

try:
    i = child.expect(['password:', pexpect.EOF], timeout=120)
    if i == 0:
        child.sendline(password)
        child.expect(pexpect.EOF, timeout=300)
    print(child.before)
    print("Transfer completed.")
except pexpect.ExceptionPexpect as e:
    print(f"Error during transfer: {e}")
    sys.exit(1)
