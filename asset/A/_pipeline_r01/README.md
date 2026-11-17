# environment-r01 재현·검수

Blender 5.3, Python 3.13, NumPy, Pillow, Pygame을 사용했다. 추가 패키지는 설치하지 않았다. 생성 도구는 ImageGen 내장 도구이며 각 sheet/prompt.txt가 최종 프롬프트다. 파일 해시는 files.sha256.json, 원본 근거는 source_evidence.json이다.

## 경로와 실행

`build_assets.py`는 이 폴더의 상위 A 폴더를 기준으로 7개 에셋을 찾는다. 검토된 입력 시트·assets.json·reference/와 SPRITE_PNG.py가 필요하다. 새 revision은 작업 사본에서 만든다. 다음 명령은 A 폴더에서 실행한다.

```powershell
& 'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe' --background --factory-startup --disable-autoexec --threads 2 --python-exit-code 1 --python .\_pipeline_r01\build_assets.py
& 'C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe' --background --factory-startup --disable-autoexec --threads 2 --python-exit-code 1 --python .\_pipeline_r01\check_saved.py
python .\_pipeline_r01\verify_assets.py
```

검수기는 창을 열지 않는다. SDL dummy는 실제 디스플레이 성능 시험이 아니다. lighting.py는 프로젝트의 기존 BRDF 그대로다. 128px 좌표 격자만 검수 호출에서 현재 셀 크기로 교체한다. 게임에 새 로더나 물리 시스템을 설치하지 않는다.

## 묶음·복원

ZIP은 A 폴더를 루트로 하며 상대 경로를 보존한다. files.sha256.json의 파일을 포함한다. 별도 폴더에 압축을 풀고 각 SHA256을 검사한 뒤 사용한다. bundle.source.json은 ZIP 해시와 manifest 서명을 가진다. 기존 제작 모델이 없었으므로 versions/에 소급 버전을 만들지 않았다.

## 관문

- 문서·원본 해시, 정적 메시·UV 존재, 7개 저장본 재개방, packed/external 일치, 임의 seek, 49셀 데이터 계약: PASS.
- 시트는 스타일·주요 형상 참고다. A01/A07의 방향 표기 충돌은 제작 기록에서 채택 패널과 축으로 정리했다. Blender 정투영 판이 최종 축 기준이다.
- 체크 타일 UV 늘어짐 시각 판정, 모션·접촉·취소·효과 1회 실행, 플레이어 착지·수면 이음새, 게임 캐시/업로드/실기 60fps: NOT_RUN 또는 DEFERRED.
- 이동 광원 CPU 재조명 16.7ms 예산: FAIL. 동적 광원 양산 전 캐시·출력 크기·비용을 조정해야 한다.
- DEC-06 양산, 새 8자리 ID, 실제 충돌 크기는 미확정이다. 부력·수영·산란은 현행 제외 범위다.
- OS 썸네일과 Blender 확장 캐시 쓰기는 샌드박스에서 거부됐지만 전달 파일 저장에는 영향이 없었다.
