# framework-r4 · Z 회전 리그

`toktogi_framework_r4.blend`에서 `SET_RUNTIME_POSE.py`의 `select_runtime('ground_spin_left')` 또는 `select_runtime('ground_spin_right')`를 사용한다. framework-r3를 입력으로 `build_spin_r4.py`를 Blender 5.3 백그라운드에서 실행하면 좌우 Action과 중간 120셀의 5패스를 출력한다.

[복원 지도](../versions/restore_map.json)에 따라 framework-r3의 Blend, `runtime_poses.json`, `toktogi_runtime_poses.zip`을 작업 폴더에 함께 복원한다. 제작 스크립트는 스크립트가 있는 폴더에 출력한다. 별도 작업 폴더에 스크립트를 복사해 실행한 뒤 검증한 ZIP과 `.source.json`을 실행 프로젝트로 옮긴다. [실행 프로젝트의 갱신 절차](../../../../../prototype/README.md)

R1/R2 발목이 교대하는 구간에서 두 발 목표 사이 여유를 늘렸다. 지지 구간 안에서는 각 목표를 월드 좌표에 유지한다. 양방향 Z는 62셀·1.55초이며 양끝 중립 자세를 공유한다.

저장된 Blend를 다시 열어 120셀의 지오메트리 해시를 대조했다. 2.5ms 간격의 좌우 각 977자세에서 출력 키의 가시적인 다리 간 교차는 왼쪽 6→0, 오른쪽 4→0자세였다. 키 사이에서는 왼쪽 95→19, 오른쪽 56→0자세였다. 지지발 높이 오차와 몸통·관절 교차 수치는 `spin_interkey_validation.json`에 기록했다.
