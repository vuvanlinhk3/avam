import subprocess
import sys
import os
import argparse

def apply_fade_test(input_file, output_file, fade_in=10, fade_out=10):
    input_file = os.path.abspath(input_file)
    output_file = os.path.abspath(output_file)
    
    # Đường dẫn ffmpeg trong dự án
    ffmpeg_path = os.path.join(os.path.dirname(__file__), '..', 'ffmpeg', 'bin', 'ffmpeg.exe')
    ffprobe_path = os.path.join(os.path.dirname(__file__), '..', 'ffmpeg', 'bin', 'ffprobe.exe')
    
    if not os.path.exists(ffmpeg_path):
        print(f"❌ Không tìm thấy ffmpeg tại: {ffmpeg_path}")
        return False
    
    print(f"Sử dụng ffmpeg: {ffmpeg_path}")
    
    if not os.path.exists(input_file):
        print(f"❌ File không tồn tại: {input_file}")
        return False
    
    # Lấy thời lượng bằng ffprobe
    probe_cmd = [ffprobe_path, '-v', 'error',
                 '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1',
                 input_file]
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        duration = float(result.stdout.strip())
        print(f"✅ Thời lượng file: {duration:.2f} giây")
    except Exception as e:
        print(f"❌ Lỗi khi lấy thời lượng: {e}")
        return False
    
    fade_out_start = max(0, duration - fade_out)
    filter_str = f"afade=t=in:st=0:d={fade_in},afade=t=out:st={fade_out_start}:d={fade_out}"
    print(f"Filter: {filter_str}")
    
    # Xác định codec và container dựa trên phần mở rộng output
    ext = os.path.splitext(output_file)[1].lower()
    if ext == '.mp3':
        codec = 'libmp3lame'
        bitrate = '192k'
    else:  # mặc định dùng AAC với container .m4a
        codec = 'aac'
        bitrate = '192k'
        if ext not in ['.m4a', '.aac']:
            output_file += '.m4a'  # thêm đuôi nếu chưa có
            print(f"⚠️ Đuôi không hợp lệ cho codec AAC, tự động thêm .m4a: {output_file}")
    
    cmd = [
        ffmpeg_path,
        '-i', input_file,
        '-af', filter_str,
        '-c:a', codec,
        '-b:a', bitrate,
        '-y',
        output_file
    ]
    
    print(f"Đang chạy lệnh: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        if result.returncode != 0:
            print(f"❌ FFmpeg lỗi với mã {result.returncode}")
            print("STDERR:")
            print(result.stderr)
            return False
        print(f"✅ Thành công! File đầu ra: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi chạy ffmpeg: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test fade in/out với ffmpeg')
    parser.add_argument('input', help='File âm thanh đầu vào')
    parser.add_argument('output', help='File đầu ra (nên có đuôi .m4a hoặc .mp3)')
    parser.add_argument('--fade-in', type=float, default=10, help='Thời gian fade in (giây)')
    parser.add_argument('--fade-out', type=float, default=10, help='Thời gian fade out (giây)')
    args = parser.parse_args()
    
    apply_fade_test(args.input, args.output, args.fade_in, args.fade_out)