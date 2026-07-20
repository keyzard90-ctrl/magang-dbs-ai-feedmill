import imageio
import sys
import os
import time

input_file = "Hasil_Final_AI_13Menit_Truck_Sack.mp4"
output_file = "Hasil_Final_AI_13Menit_Compressed.mp4"

print(f"Waiting for {input_file} to be ready...")

# Wait until the file stops growing (meaning the generating script has finished)
def wait_for_file_to_finish(filepath, timeout_mins=120):
    start_time = time.time()
    last_size = -1
    stable_count = 0
    
    while time.time() - start_time < timeout_mins * 60:
        if os.path.exists(filepath):
            current_size = os.path.getsize(filepath)
            if current_size == last_size and current_size > 1000000:
                stable_count += 1
                if stable_count >= 10: # 50 seconds of no size change
                    return True
            else:
                stable_count = 0
                last_size = current_size
        time.sleep(5)
    return False

print("Monitoring file size...")
if wait_for_file_to_finish(input_file):
    print(f"File seems ready. Starting compression to {output_file}...")
    try:
        ffmpeg_path = "/Users/macbookpro/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-x86_64-v7.1"
        command = [
            ffmpeg_path,
            "-y", 
            "-i", input_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            output_file
        ]
        
        print("Starting ffmpeg compression...")
        import subprocess
        subprocess.run(command, check=True)
        print("Compression finished successfully!")
        
        # Close the uncompressed video if it was opened by the other script (QuickTime)
        os.system("killall 'QuickTime Player'")
        
        # Open the new compressed video
        os.system(f"open {output_file}")
    except Exception as e:
        print(f"Error during compression: {e}")
else:
    print("Timeout waiting for file.")
