# Windows 실행 파일 (.bat)

보통은 저장소 맨 위의 **`START_HERE.bat`** 하나만 더블클릭하면 된다. 메뉴에서 번호를 고르면 아래 파일이 실행된다.

| 메뉴 | 파일 | 하는 일 | 필요 |
|---|---|---|---|
| 0 | `00_setup.bat` | uv 설치 → Python 환경(`.venv`) 생성 → 패키지 확인 | 인터넷 (처음 한 번) |
| 1 | `01_view_model.bat` | MuJoCo 3D 뷰어로 원본 모델 보기 (5종 장면 + 직접 경로) | 0 |
| 2 | `02_check_torque.bat` | 질량·관절 범위·자세 유지 토크 점검. 서보(XL330/MG996R/MG90S/SG90)·전압·자세 선택, 결과는 `logs\` | 0 |
| 3 | `03_build_bom.bat` | `bom\build_bom.py` → BOM.xlsx·csv 재생성 후 Excel로 열기 | 0, Excel 닫아 두기 |
| 4 | `04_plates_dxf.bat` | 판재 4종 DXF·미리보기 PNG 재생성 (`cad\plates\dynamixel`) | 0 |
| 5 | `05_joint_frames.bat` | 관절 위치·축·링크 길이 추출 (1배·1.5배) → Fusion 매개변수 CSV | 0 |
| 6 | `06_render_images.bat` | 모델 3방향 렌더 이미지 → `renders\` | 0 |
| 7 | `07_update.bat` | GitHub에서 최신 받기 (`git pull`) + 패키지 갱신 | Git |
| 8 | `08_get_reference_repos.bat` | 참고 저장소를 `external\`로 받기: microduck_rl, microduck 런타임, Open Duck Mini | Git |
| 9 | `09_policy_sim.bat` | 학습된 걷기 정책(.onnx)을 키보드로 조종 (시뮬레이션) | 8, **Windows에서는 실험적** |
| 10 | `10_train_walk.bat` | 걷기 정책 학습 (로컬 GPU 또는 Hugging Face Jobs) | 8, NVIDIA GPU, **Ubuntu/WSL2 권장** |

- `_env.bat`은 공용 설정이라 직접 실행하지 않는다.
- 9·10은 Pollen의 `microduck_rl`이 Linux + CUDA 기준이라 Windows에서 설치가 실패할 수 있다.
  그때는 Ubuntu 노트북이나 WSL2에서 `plan.md` 6절 명령을 그대로 쓴다. 10번의 HF Jobs 모드는 클라우드 GPU라 Windows에서도 된다(유료, `hf auth login` 필요).
- `external\`, `logs\`, `renders\`, `.venv\`는 git에 올라가지 않는다.
- 배치 파일은 인코딩 문제를 피하려고 영어 메시지만 쓴다.
