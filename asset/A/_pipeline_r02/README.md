# environment-r02 재현·검수

Blender 5.3, Python 3.13, NumPy, Pillow, Pygame. 추가 의존성 설치 없이 기존 환경을 사용했다. 스크립트는 자신의 상위 A 폴더에서 입력·출력을 찾는다. 원본 프로젝트에 바로 재생성하지 말고 ZIP을 별도 작업 폴더에 복원한 뒤 실행한다.

```powershell
& 'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe' --background --factory-startup --disable-autoexec --threads 2 --python-exit-code 1 --python .\_pipeline_r02\build_assets.py
& 'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe' --background --factory-startup --disable-autoexec --threads 2 --python-exit-code 1 --python .\_pipeline_r02\check_saved.py
python .\_pipeline_r02\verify_assets.py
python .\_pipeline_r02\make_previews.py
python .\_pipeline_r02\finalize.py
```

각 명령 성공 후 다음 명령을 실행한다. build_assets는 셀과 manifest를 다시 쓰므로 반드시 make_previews까지 실행해 5패스 아틀라스·좌표·해시를 갱신한다. finalize는 검증 결과·Blend·생성기 해시 일치를 요구하고 문서·ZIP을 작성한다. OS 썸네일/확장 캐시 경고는 전달 파일 저장과 무관했다.

## 소비 규칙

- 2D/environment-r02/manifest.json의 cells에서 view를 선택하고 cell_size·pass_order·pivot·anchors를 읽는다. 000.png는 5패스 적층 원본, sprite.png는 표시용이다.
- game_atlas는 3×3 배치·2px 패딩과 각 rect를 명시한다. 게임 9뷰만 포함하며 6개 ortho_*는 개별 셀로 남는다. 데이터 패스 coverage는 Base Alpha다.
- turntable.png는 8방향 APNG 검수 미리보기이며 게임 클립이 아니다. 시간 350ms/방향. 호환 right는 순환 순서에 끼워 넣지 않는다.
- Blender 내장 SELECT_ENVIRONMENT_VIEW.py를 실행한 뒤 select_view('yaw_090')처럼 호출한다. ENVIRONMENT_VIEWS.json에 고정 카메라/피벗·yaw가 들어 있다. 자동실행은 필요 없다.
- lighting.py는 기존 게임 BRDF 사본이다. 검수기에서 좌표 격자 크기만 해당 셀로 바꾼다. 실기 성능 검증이나 새 런타임 로더를 대체하지 않는다.

## 복원·이전 자료

files.sha256.json은 ZIP 내부의 상대 경로와 SHA256을 잠근다. bundle.source.json은 ZIP 해시와 파일 목록 서명을 가진다. 별도 폴더에 안전하게 풀고 해시를 확인한 후 사용한다. r02 ZIP은 r02 모델·출력과 필요한 입력을 포함하며 전체 프로젝트/게임 실행 묶음이 아니다. 이전 r01 결과는 원래 프로젝트 위치와 r01 ZIP에 보존하며 restore_map.json에 연결했다.

before/의 Markdown은 이전 색인의 원문 보존본이다. 그 안의 상대 링크는 이전 A 위치를 기준으로 하므로 탐색에는 현재 ASSET_INDEX.md를 사용한다. reference/는 제작 당시 문서/이미지 스냅샷이다. 원본 생태·모션·라이선스 근거는 기존 document 및 r01 제작 기록을 유지하며 새 생물 사실을 추가하지 않았다.

## 남은 관문

큰 셀 로더·상태/충돌/접지 연결·실기 60fps·실제 코스·물리/효과는 미검증이다. CPU 동적 재조명은 측정 예산을 넘는다. 수영·부력·산란은 현행 제외 범위를 유지한다. 정적 모델 개선을 모션 구현으로 간주하지 않는다. 돌 측면 UV와 작은 부위의 밀도 차이는 고유 방향성 텍스처를 확대 적용하기 전에 재전개한다. 번호 확정·DEC-06 양산은 보류다.
