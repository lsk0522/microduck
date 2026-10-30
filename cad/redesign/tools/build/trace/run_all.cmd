@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\LSK0522\Desktop\Microduck"
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py power_support >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py yaw2roll >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py hip_l >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py upper_leg_left >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py upper_leg_right >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py leg >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py ankle_left >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py ankle_right >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py foot_left >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py foot_right >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py neck_pitch >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py yaw_roll_motion >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py face_part >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py motor_support >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py noenoeil >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py m12_lens_holder >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py soft_mouth_top >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py jaw_soft >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py sole_left >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py sole_right >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py right_shell >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py left_shell >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py bottom_head_shell >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py jaw >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
"C:\Users\LSK0522\Desktop\Microduck\.venv\Scripts\python.exe" cad\redesign\tools\trace_part.py top_head_shell >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt" 2>&1
echo ALLDONE >> "C:\Users\LSK0522\Desktop\Microduck\cad\redesign\tools\build\trace\trace_log.txt"
