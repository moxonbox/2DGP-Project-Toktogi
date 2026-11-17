# ToktogiPrototype Pico2D 재구현 명세

2026-11-17 · v1.3 · **Pico2D 후보 구현 / 자동 검증·추가분 집중 검사 / 실기 미검증**. 현행 framework-r4의 게임 규칙과 integrated-r5·framework-r4 에셋을 승계한다.
목표는 재사용 가능한 모듈, 360° 회전·동작 연결, 128px 5패스 조명을 보존하고 개구리밥·연꽃잎의 두 Level을 끊김 없이 연결하는 것이다.

## 1. 기준과 문서 분담

| 기준 문서 | 소유 내용 |
| --- | --- |
| 이 문서 | 채택 범위·현행 차이·모듈 경계·이식 순서·인수·배포/복원 |
| [Control](Control.md#atlas-controls) | 플레이/F2 키·버튼·검색·입력 시각·순서·취소·포커스·C-01~08 |
| [Pico2DBackend](Pico2DBackend.md) | SDL 큐·좌표/DPI·RGBA·폰트·자원 수명·B-01~05 |
| [StageLevel](StageLevel.md) | 월드/구간·Camera·대상/지지 키·목표·체크포인트·로딩·S-01~06 |
| [2Dshader](2Dshader.md#atlas-materials) | CPU 재질·Normal 비교·Emissive/Bloom 수식·픽셀 기준 |
| [통합 기획](game-design/001_toktogi_game_design_spec.md) | [시스템](game-design/011_toktogi_system_design_spec.md)·[콘텐츠](game-design/012_toktogi_content_design_spec.md)·[전투](game-design/013_toktogi_combat_design_spec.md)의 범위·수치·인수 |
| [프레임워크](game-design/021_toktogi_game_framework_spec.md)·[상태 머신](game-design/toktogi_state_machine.md#atlas-states) | 현행 호출·독립 상태·모션 전이·구현 이력 |
| [플레이 v2.1](game-design/022_toktogi_playable_action_animation_spec.md) | 원안·요구 ID·제작/효과 계약·채택/보류 결정 |
| [AssetPipeLine](AssetPipeLine.md)·[번호](AssetLabelRule.txt)·[크기](AssetSize.md) | 스타일·식별·체장/BU/px·출력·패킹·검수·복원 |

- 같은 사항은 현재 사용자 요구, 이식 채택 결정, 위 소유 문서, 과거 검토 순으로 해석한다. 현재 구현 사실과 차기 요구가 다르면 양쪽 상태·근거를 남긴다.
- 중복 규칙은 소유 문서에서 수정하고 여기서는 핵심 수치와 관문을 연결한다. 원안의 선택 기능·생물 관찰·이전 키 배치를 현행 요구로 자동 승격하지 않는다.
- 이번 범위는 Rebuild 통합 보완과 관련 문서 정합이다. 상세 원안·요구 ID·기존 앵커를 유지하며, 문서 변경을 코드 수정이나 구현 합격으로 기록하지 않는다.

## 2. 파일 대조로 확인한 상태

| 확인 대상 | 사실·문제 | 반영 기준 |
| --- | --- | --- |
| 실행본 | `toktogi/prototype/`는 Pygame이며 `prototype_pico2d/`는 아직 없다. main이 App을 먼저 import한다. | `--verify`의 무영상 실행과 전이 import 제거를 R-03에서 확인한다. |
| 번들 | 기본 1,444셀·보조 930셀의 ZIP SHA256이 각각 잠금과 일치한다. | 총 2,374셀의 출처·기반 서명을 보존한다. 재실행·재출력 합격과 구분한다. |
| 입력·백엔드 | Pico2D 1.5.1 기본 get_events는 시각·IME·포커스 등 필요한 정보를 보존하지 않는다. | PySDL2 원시 큐를 한 번 소비하고 Control로 변환한다. |
| 구간 콘텐츠 | 현행 Course는 단일 코스·전역 대상 상태다. 두 Level 배치·연꽃 제작물은 확인되지 않았다. | 월드 데이터·연꽃 에셋/바인딩·도달성 검증을 신규 산출물로 명시한다. |
| 문서·도구 | B의 23개 Markdown에서 깨진 로컬 링크 13곳을 확인했다. 생성기·README·잠금에는 옛 경로도 남아 있다. | 확인 가능한 문서 링크를 복구하고 원본 미보유·도구 미수정은 따로 표시한다. |

- 프로젝트의 소스·manifest·잠금·저장 검증과 C의 `rebuild_review_stage`, `pico2d_rebuild_research`, `pipeline_production_review`를 대조했다. 수정 시각만으로 최신본을 선정하지 않는다.
- 기존 [verification.json](../../toktogi/prototype/verification.json)의 13.75초·4회 도약·1회 탄성 완주는 저장된 Pygame 결과다. 이번 작업의 새 플레이 시험 결과가 아니다.
- 기존 교차 후보, 이식으로 생긴 오류, 문서 보완, 자동 검증, 실기 인수를 각각 구분한다. 근거가 없는 항목은 PASS로 바꾸지 않는다.

## 3. 포함·제외·보류

- DEC-02는 Pico2D의 실제 창·Image/Font·최종 present와 **동일 SDL2 renderer**의 CPU RGBA 업로드다. DEC-01/07의 재질 반응을 유지하며 단순 import만으로 채택 완료를 인정하지 않는다.
- 기존 보행·Q 반전·Z 지상 360°·자동 공중제비·E/F/G 작업·X 공격·진행·F2/HTML을 이식한다. 단일 코스를 비교 프로필로 보존한 뒤 두 Level과 Camera를 추가한다.
- 플레이는 발판·대상·필요 피드백을 표시하며 HUD·임의 장식 배경은 추가하지 않는다. F2 검수 UI와 수면 식물의 고체 발판 환경은 포함한다.
- 수영·부력·수면 행동·산란·지속 관계·공동 도약은 제외한다. 08 방울 손질·개체 간 관찰·수직축 공중 선회는 검수 전용이다.
- 정확한 중간 저장/복원, 동적 발판·경사 IK, 최종 생산 좌표/view/Normal/Depth 계약 DEC-06은 보류한다. 현행 실험 프로필 이식은 DEC-06 확정이 아니다.
- 신규 적 AI·HP/스태미나·다중 타격·추가 월드·오디오 콘텐츠·게임패드·키맵 편집기는 범위 밖이다. 두 Level용 에셋 제작과 게임 연결은 별도로 인수한다.

## 4. 실행 환경과 시작·종료

- 후보는 Windows x64·Python 3.11 이상, `pico2d==1.5.1`·`Pillow==13.0.0`이다. 실제 통과한 Python·PySDL2·PySDL2-DLL·SDL2/image/ttf/mixer의 버전·해시·로드 경로를 잠근다.
- 새 코드는 `toktogi/prototype_pico2d/`와 별도 가상환경에 둔다. 기존 `toktogi/prototype/`의 코드·번들·검증 결과를 비교 기준으로 보존한다.
- Pygame을 새 런타임·검증·HTML의 직접/전이 import와 설치 의존에서 제거한다. NumPy·GPU 엔진을 필수로 추가하지 않으며 CPU 계산을 GPU 셰이더로 표기하지 않는다.
- `main.py --verify`는 App import·창/SDL 초기화 전에 분기한다. 코어·Pillow 맵·RGBA·시간표 검사는 영상 장치 없이, 업로드·입력·DPI·폰트는 실기에서 확인한다.
- 선택한 가상환경으로 임의 cwd·한글/공백 경로에서 실행한다. 경로는 `__file__` 또는 명시 인자로 해석하며 `_`·C011·`paradosa` 등 실제 식별 문자열을 보존한다.
- 자동 설치·다운로드는 하지 않는다. DLL·폰트·번들 실패는 단계·경로·원인을 출력하고 비정상 종료한다. 정상 실행에는 Blender·네트워크가 필요하지 않다.
- Pico2D 1.5.1은 open_canvas 안에서 초기화와 두 번의 present를 수행한다. 생성 후 NULL 검사만으로 내부 실패가 안전해지지 않으므로 사전 의존 검사·실패 주입을 R-02에서 검증한다.
- 격자·초기 기본색 노출, 오디오 장치 부재, renderer 실패를 확인한다. 폰트/텍스처를 먼저 정리한 뒤 canvas를 닫으며 정상·예외·부분 초기화의 중복 해제를 방지한다.

## 5. 모듈 책임과 영향 범위

| 모듈 | 책임과 인계 |
| --- | --- |
| main.py·app.py | CLI·초기화/종료·장면 조립. 하나의 Assets를 플레이/F2에 주입한다. |
| input_clock.py·timeline.py | 엔진 독립 입력·시각/순번·120Hz 큐·누적 시간. SDL 타입은 입력 어댑터에서 끝낸다. |
| game.py·course.py·world.py(신규)·physics.py | 행동/효과·기존 Course·Stage/Level·월드 조회/진행·Capsule 충돌. 렌더러 없이 검증한다. |
| motion.py·replays.py | Track·MotionSet·공유 셀·게임 시간표·기록 입력. 표시가 발사·소비·타격을 실행하지 않는다. |
| materials.py | ZIP/잠금/서명·셀/마커·Pillow 5패스. convert_alpha나 화면 생성 없이 읽는다. |
| lighting.py·sprite_renderer.py | CPU 재질·접점 보정·RGBA·제한 캐시. Pico2D Texture 소유권은 갖지 않는다. |
| pico_backend.py(신규) | 단일 renderer·RGBA 업로드·Image/Font·도형·clip·좌표·원시 이벤트·해제. |
| play_view.py·motion_viewer.py | Camera·플레이 표시·F2 검색/재생/재질/마커. 게임 효과를 표시 루프에 넣지 않는다. |
| pack_assets.py·build_motion_preview.py·verify_*.py | 패킹·잠금·HTML·요구/회귀 검사. 같은 Assets·MotionSet을 사용한다. |

- 기존 공개 진입점·Course 주입·maps 제공자·리플레이를 재사용한다. 범용 ECS·플러그인 계층은 추가하지 않으며 C011 전용 로더를 모든 생물의 로더라고 주장하지 않는다.
- 의존 제거는 main/app뿐 아니라 materials·sprite_renderer·viewer·play_view·검증·HTML까지 확인한다. Start-Toktogi·requirements·도구 기본 경로도 함께 인계한다.
- Pygame 도형의 발판·그림자·먹이·씨앗·가시·F2 패널을 출력 목록에 포함한다. 창과 캐릭터만 보이는 상태를 전체 화면 이식 완료로 기록하지 않는다.

## 6. 입력·시간·취소 계약

- 키·버튼은 [Control](Control.md) 그대로다. 물리 키·논리 명령·DOWN/UP·repeat/modifier·SDL 시각·수집 순번·도전/장면 세대를 보존한다.
- 단일 원시 SDL 큐를 쓰며 Pico2D get_events와 중복 소비하지 않는다. 프레임 시계와 시각 기준점을 맞추고 32비트 순환·지연 입력을 처리한다. TEXTINPUT/TEXTEDITING을 키 문자 변환으로 대체하지 않는다.
- 정렬은 정규화 시각·순번이다. 전환/물리/위험 후 tick 입력, 이어 발사·작업·타격을 처리한다. close 뒤 같은 틱의 나머지 입력은 틱 뒤로 넘기는 현행 순서를 보존한다.
- [Timeline](../../toktogi/prototype/timeline.py)의 `STEP=1/120`, `max_ticks=240`과 남은 accumulator를 유지한다. 3초 지연을 2초 처리한 뒤 남은 1초를 회수하며 시간을 조용히 버리지 않는다.
- 게임·전역 단발키의 반복 DOWN·고립 UP은 무효다. 좌우 Shift는 물리 키 집합으로 관리한다. F2의 목록/프레임/Backspace 반복과 토글 1회 정책을 구분한다.
- Pause/F2/포커스 상실/R에서 유지키·미실행 예약과 이전 문맥의 게임 입력을 정리한다. 새 DOWN부터 수락하고 합성 Space UP·뒤늦은 옛 세대 입력으로 도약/효과를 만들지 않는다.
- Playing에서만 새 행동을 수락한다. Paused는 표시 셀·물리를 고정하며 Failed/Cleared는 새 효과를 차단한다. 이미 확정된 효과는 취소로 되돌리지 않는다.
- Level 경계는 입력 문맥 종료가 아니다. Space 짝·F/G 유지·Q/Z 예약·Action/Track 시간을 이어 가고 실제 취소 조건만 적용한다. C-01~08로 경계·IME·DPI까지 확인한다.

## 7. 보존할 게임·모션 수치

- 보행 24/회복 13.2px/s, 가속 760·무이동 감속 1,200·Shift 제동 1,700px/s². 수직 Capsule 반경 14·높이 52px, 중력 850px/s²·최대 하강 660px/s를 유지한다.
- 일반/탄성 상승 기준 426/541px/s, 준비 80/45ms, 탄성 입력 창 착지 전 100/후 165ms다. 속도 합산·조준·회복 계수 0.82는 [시스템 식](game-design/011_toktogi_system_design_spec.md)을 따른다.
- 준비 승인 때 방향·조준·속도·지지를 보관하고 발사 때 지지를 재검사한다. 발사/착지의 요청 소비와 공중 추가 추진 금지를 유지한다. 착지 표본 재도약은 연결 트랙 길이를 따른다.
- 강착지는 하강 충격 >370px/s에서 270ms, 나머지는 190ms 회복이다. Q 중립 480ms·지지 자세 각 100ms, Z 본편 1.55초·62셀을 유지한다.
- 공중제비는 게임 330ms·역위 105ms·전개 핵심 100ms다. 착지/천장/피격이 중단하며 시각 회전은 Capsule 축·추진을 바꾸지 않는다. 8개 yaw와 호환 right를 미러로 대체하지 않는다.
- Q/Z 지지 부족·모서리 방향 반전·보행 위상별 제동·회전 종료 예약 재검사를 보존한다. F/G 예약은 유지 중일 때만 유효하며 마지막 수락 요청을 따른다.
- 06–07 손질 3.96초, 6발→4발→오른쪽 3발 지지, 더듬이 접촉 반응·공유 셀·홀드·표본별 취소 복귀를 유지한다. obs_jump Root 이동을 게임 위치에 중복 적용하지 않는다.
- E 효과 200ms·접점 3.5px 재검사, F 준비 160ms·400ms 주기 중 220ms 소비·초기 먹이 4회분이다. E 해제는 승인된 단발을 끊지 않고 F 해제는 미실행 소비를 취소한다.
- X 활성 `[78,162)ms`·종료 360ms는 본편 시작 기준이다. F→X 진입 ≤75ms와 타격 자세 홀드 `[75,175]ms`는 효과창을 늦추거나 중복시키지 않는다.
- 가시 접촉 우선·1회 타격·넉백·피격 제한은 [전투](game-design/013_toktogi_combat_design_spec.md)를 따른다. 작업 가능색과 수락 조건을 일치시키며 거절 틴트 180ms·Sprite Alpha와 충돌을 구분한다.
- 레거시 클리어는 등불 활성·목표 지지·`839<x<940`·`abs(vx)<1`의 200ms 유지다. 실패 `x<−68/x>1028/y>585`와 체크포인트/R은 [콘텐츠](game-design/012_toktogi_content_design_spec.md)의 단일 코스 기준이다.

## 8. 에셋·재질 데이터 인계

- [색인](../../asset/C/C011_toktogi/ASSET_INDEX.md)·[통합 Blend](../../asset/C/C011_toktogi/3D/toktogi_unified.blend)는 제작 출처다. 이식만으로 UV·리그·텍스처를 재제작하거나 기존 출처 해시를 통합본 해시로 바꾸지 않는다.
- 실행 기준은 [기본 ZIP](../../toktogi/prototype/toktogi_assets.zip)·[보조 ZIP](../../toktogi/prototype/toktogi_runtime_poses.zip)과 각각의 `.source.json`이다. ZIP 해시·revision·기반 서명·출처를 묶음으로 검사한다.
- 128×128의 sprite/base/normal/rm/emissive를 128×640 PNG에 적층한다. Sprite는 sRGB/straight Alpha, Base는 sRGB/coverage, Normal·RM·Emissive는 선형 데이터다.
- Normal/RM/Emissive 저장 A=255를 coverage로 쓰지 않는다. Base A로 마스킹하며 패스 Alpha를 일괄 동일화하지 않는다. Normal은 R 오른쪽·G 위·B 카메라 방향이고 RM은 R 거칠기·G 금속성이다.
- 원본 82클립+17전환+보조 146프로필=245, 게임 시간표 12+리플레이 4=기존 261항목이다. 신규 경계 리플레이는 별도 집계하고 클립·Action·뷰·셀 수를 혼동하지 않는다.
- 제작 공중제비 680ms와 게임 330ms를 통일하지 않는다. Game/F2/HTML은 같은 게임 시간표·리플레이를 쓰며 원본 검수는 제작 시간을 사용한다.
- 중복 ZIP 이름/셀 키, 누락·손상 PNG, 크기/패스/rect, 유한 좌표·양수 시간·지원 방향·마커·전환 참조·서명을 검사한다. 미지원 입력을 idle로 숨기지 않는다.
- 현행 로더의 PNG 헤더 검사와 전체 디코딩 검사를 구분한다. 변경 묶음은 전 셀 디코딩·CRC·참조 정합을 검증하고 시작 시 사용할 캐시의 허용량도 기록한다.
- 06 접점 잉크·06–07 공유 경계·작업/지지 마커·의도한 Base/Sprite 1px 차이를 보존한다. 픽셀 보정은 셀·좌표·패스·사유를 남기며 표면/마커 오류를 장식으로 숨기지 않는다.
- C011의 팔레트·외곽선·눈·웨더링은 [AssetPipeLine](AssetPipeLine.md)의 최종 출력기 기준이다. 초기 외부 출력기를 그대로 재사용하지 않으며 런타임 연속 조명을 13색으로 강제하지 않는다.
- 신규 에셋은 ID·생물 크기/연출 배율·셀·충돌·모션·게임 바인딩을 함께 인계한다. C011의 128px·필수 모션 고정 제약과 번호 규칙 미정을 명시한다.

## 9. 화면·업로드·성능 계약

- 논리 필드 960×560, 창 1280×744, 필드 오프셋 (160,92), 피벗 (64,88), 플레이 1×·F2 1×/2×/3×를 유지한다. 필드는 확장 월드의 전체 경계가 아니다.
- `screen=FIELD_origin+round(world−camera)−pivot×scale`로 표시한다. Pico2D 목적 좌상단은 `draw_to_origin(x,H−y−h,w,h)`로 한 번 변환하고 물리 실수 좌표는 유지한다.
- 창/renderer 출력 크기·viewport·DPI·입력 역변환·clip을 [백엔드](Pico2DBackend.md#backend-coordinates)로 검증한다. 문자·도형·마커·광원에도 같은 변환을 쓰며 API y축 때문에 Normal G를 뒤집지 않는다.
- RGBA8·RGBA32·pitch 행 복사·Nearest·straight Alpha·그리기 순서를 유지한다. 업로드 실패/잠금 해제·clip 복원·Image/Font 단일 소유권을 검사한다.
- PLAY_CLEAR=(99,108,112), 플레이 power=.82·ambient=.34와 기존 CPU BRDF·감쇠·윤곽·접점·눈 하이라이트를 먼저 일치시킨다. F2에는 자체 배경·광원 설정을 적용한다.
- F2 평탄 Normal은 디코딩 후 정확한 (0,0,1)이다. Bloom은 초기 꺼짐이며 발광만 선형 합성한다. 6px 여유·피벗·프리뷰 clip·UI 제외·검은 발광 음성 대조는 [2Dshader](2Dshader.md)를 따른다.
- 맵 36셀·표면 계산 24셀·조명 96셀·글자 512항목은 비교 상한이다. 새 텍스처/Bloom 상한은 기준 장치 측정으로 정하고 eviction·종료 때 해제한다.
- 2,374셀의 5패스 RGBA 전량은 약 741.9MiB다. 캐시·임시 복사·텍스처·폰트·Bloom은 추가 비용이며 압축 ZIP 크기로 메모리를 판정하지 않는다.
- 로딩/워밍업과 정상 프레임의 계산·업로드·합성 비용을 분리한다. 장치·OS·Python/DLL·renderer·DPI·해상도·vsync·제한 설정과 120프레임 p95/최대를 남긴다.
- 60fps 목표의 처리 예산은 16.7ms다. 의도적 대기와 처리 비용을 구분하고 p95 목표·최대 지연 허용값·메모리 상한을 시험 전에 정한다. 목표 미달은 실기 인수 미완료다.

## 10. 두 Level의 연속 전환

- `stage_01/pond_duckweed`와 `stage_02/lotus_leaf`는 제작 식별자다. World는 시간/좌표/물리, Stage는 목표/진행, Level은 배치/충돌/표시 단위이며 App 장면은 계속 플레이다.
- 연꽃의 종·asset_id·제작 파일·표시 크기·충돌/모션 바인딩은 신규 확정 항목이다. 기존 개구리밥 또는 임시 도형을 최종 연꽃 제작물로 집계하지 않는다.
- Stage/Level revision·offset·bounds·플랫폼/대상 키·포털 방향/영역·목표·실패·체크포인트·필수 에셋을 명시한다. 구체 치수와 도달 입력이 없는 예시를 완성 코스로 처리하지 않는다.
- 기존 Course는 동일 값의 단일 World 프로필로 감싼다. 새 월드는 인접 구간을 함께 조회하고 support/prep의 객체 동일성 비교와 전역 bool/먹이 개수를 안정적인 키별 상태로 함께 이식한다.
- 공유 발판은 하나의 충돌체다. 틱 전후 이동 구간으로 실제 경계 통과를 판정하고 겹친 포털 우선순위·왕복 진동·중복 진입을 처리한다. R 재배치는 일반 통과 이벤트가 아니다.
- 위치·속도·방향·지지·회복·준비·탄성 창·Action·Track 시각·대상 참조·입력 세대를 보존한다. 작업/타격은 기존 접촉 조건을 재검사하며 경계 진입으로 효과를 다시 발생시키지 않는다.
- Camera·객체·광원은 같은 월드 변환을 사용한다. 연결 양쪽 발판을 미리 보여 주고 Level별 clamp·줌·광원 초기화로 스냅하지 않는다. 기존 코스 Camera는 (0,0)이다.
- 첫 두 Level은 시작 전 검증/준비한다. 전 셀 상주 대신 연결부 가시 데이터·예상 포즈를 제한 캐시에서 준비하며 경계에 I/O·압축 해제·워밍업을 몰지 않는다.
- 중간 Stage 완료와 최종 Cleared를 구분한다. 체크포인트는 명시 지지/방향/선행 목표로 R을 시작하고 가변 도전 상태를 초기화한다. 정확한 중간 저장 복원은 요구하지 않는다.
- S-01~06은 레거시 완주, 보행/도약/공격 중 경계, 왕복·Pause/F2·실패/R, 데이터 누락·중복 키·도달 불가, 화면/광원과 최초·재통과 비용을 검증한다.

## 11. 구현 순서와 완료 관문

| 관문 | 완료 조건·증거 |
| --- | --- |
| R-01 기준 고정 | 소스·번들/잠금·입력·코스·RGBA·요구 상태의 해시와 기준 장치를 기록한다. 저장 결과와 새 실행 결과를 분리한다. |
| R-02 환경/백엔드 | 단일 창/renderer·Pico2D Image·한글·RGBA/pitch·Nearest·DPI/clip·원시 입력·초기화 실패·종료의 B-01/02/04를 확인한다. |
| R-03 코어/입력 | Pygame 없는 코어·Assets·CLI/HTML, 120Hz·C-01~04/06, Course 주입·안정 지지/대상 키를 검증한다. |
| R-04 모션/월드 | Q/Z·F→X·06–07·2,374셀·기존 261항목과 새 경계 리플레이, 신규 에셋·두 Level·Camera·S-01~06을 대조한다. |
| R-05 재질/도구 | 기존 RGBA를 맞춘 뒤 Normal/Bloom·C-05/07/08·B-03을 추가하고 패커·HTML·회귀의 무영상 실행을 확인한다. |
| R-06 실기/성능 | 실제 키·IME·포커스·시작 위상·장시간 전환·오류 정리·B-05를 검사한다. 메모리/최대 지연과 16.7ms 목표를 판정한다. |
| R-07 배포/복원 | 깨끗한 환경·임의 cwd에서 실행/검증한다. 코드·두 ZIP/잠금·의존성·설치/시작 문서·HTML/구조도를 같은 revision으로 전환·복원한다. |

- 각 관문은 요구 ID·기대/실제·허용 오차·시험 환경·입력/픽셀 근거·미검증 사유를 남긴다. 기존 72개 요구 ID와 새 R/C/B/S를 연결하고 보류를 PASS 개수에 포함하지 않는다.
- 10/15/20/30/60fps·시작 위상별로 상태·방향·지지·위치/속도·효과 횟수/시각을 대조한다. 이산 결과는 일치하고 실수/시각 오차는 해당 기존 시험의 허용값을 확대하지 않는다.
- CPU 기준 RGBA는 Alpha 차이 0·RGB 채널 최대 1/255, SDL 최종 합성은 고정 배경 표본으로 별도 대조한다. 텍스트는 글리프·크기·배치·잘림도 검사한다.
- 128px의 Q/Z·정점/착지·섭식/공격·06–07에서 접지·접촉·공유 경계·눈·잘림을 확인한다. 저표시율 누락은 표본/홀드/진폭과 효과 실행을 분리해 추적한다.
- F2/HTML의 재생은 게임 효과를 재실행하지 않는다. 자급형 HTML·모션 수·시각/셀·리플레이 결과를 검증하고 과거 Pygame PASS를 새 백엔드 합격으로 복사하지 않는다.

## 12. 경로·배포·복원

- 후보 코드·World 배치·기본/보조 ZIP·잠금·폰트 정책·의존성·검증 결과를 한 revision으로 보관한다. 기존 해시를 보존한 이식과 에셋을 다시 만든 변경을 구분한다.
- 패커는 스크립트 옆 ZIP을 갱신하며 ZIP과 잠금을 순차 교체한다. 실행 중인 디렉토리에 패킹하지 말고 후보에서 두 파일을 검증한 뒤 전체 실행 묶음을 전환한다.
- [시작 스크립트](../../toktogi/prototype/Start-Toktogi.cmd)·[README](../../toktogi/prototype/README.md)·requirements·패커/HTML 기본 경로·배포 ZIP을 함께 갱신한다. Pygame이 없는 환경에서도 통과해야 한다.
- [구조도 생성기](../tools/architecture/build_atlas.py)의 SPEC은 `markdown/game-design/001_toktogi_game_design_spec.md`로, C01 참조는 실제 C011 경로로 수정해야 한다. 현재 생성 HTML만 수동 수정하지 않는다.
- 구조도의 9개 원본 ID·Control의 두 표·상태 머신 앵커/도표·[통합 원본 계약](game-design/001_toktogi_game_design_spec.md#atlas-sources)을 보존한다. 도구 README·기존 런타임 README/요구 추적·잠금의 옛 경로도 인계 검사에 포함한다.
- 손상 ZIP·누락 폰트·중도 실패에서 이전 실행본이 보존되어야 한다. 전환 전 백업 경로·해시를 확인하고 실패하면 코드·번들·잠금·의존성을 함께 복원한다.
- 이번 문서 수정은 생성기 수정·HTML 재생성·런타임 전환을 수행한 것이 아니다. C의 조사 근거를 배포에 포함할 때는 필요한 파일을 보관하고 기기 종속 상대 링크를 갱신한다.

## 13. 구현 후 재현과 잔여 범위

아래는 **후보 구현 완료 후** 프로젝트 루트에서 실행할 명령이다. 기본/보조 ZIP·잠금을 후보 폴더에 함께 배치한다. 현재 후보 경로의 존재나 통과를 뜻하지 않는다.

```powershell
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/main.py --verify
toktogi/prototype_pico2d/.venv/Scripts/python.exe toktogi/prototype_pico2d/build_motion_preview.py asset/C/C011_toktogi/2D/integrated-r5 toktogi/prototype_pico2d/ToktogiMotionPreview.html
```

- 저장된 [07·08 지오메트리](../../asset/C/C011_toktogi/2D/integrated-r5/geometry_validation.json)의 r5 07 후보 30쌍과 [Z 연속 자세](../../asset/C/C011_toktogi/3D/framework-r4/spin_interkey_validation.json)의 r4 왼쪽 19자세는 제작 QA 잔여다. 후보를 실제 관통으로 단정하거나 이식만으로 해결 처리하지 않는다.
- DEC-06·정확 저장/복원·동적/경사 IK·번호 규칙 미정은 계속 보류한다. 새 교차·피벗 튐·명암 저하는 기존 잔여와 구분해 수정한다.
- v1.2 확인 범위는 문서/소스 대조, 로컬 링크·앵커·구조도 입력 형식, 번들 해시·개수·정합 검사다. 새 Pico2D 설치·게임 실행·Blender 재개방·실기/성능 검사는 수행하지 않았다.

## 14. 2026-11-17 추가 구현과 최신 상태

- `toktogi/prototype_pico2d` 후보를 구현했다. 위 v1.2 조사 시점의 미구현 기록은 기준 이력이며 최신 상태는 후보 README/검증 JSON을 따른다.
- 기본 `pond_test`는 수면 위 시험 연잎 6개와 C261의 간헐적 입 돌출·도약 공격이다. 경고 후 고정 위치를 공격하며 Space로 회피, E/X로 반격한다.
- 플레이 조작은 WASD와 상황별 E(가까운 적 공격 우선·활성/수집·섭식·손질)로 변경했다. 기존 화살표/F/G 입력은 원본 회귀 fixture에만 남긴다.
- C261은 asset의 male/right 6액션 72셀·mouth_tip을 재사용한다. 최종 연꽃 에셋 부재로 연잎은 시험 도형이며 양산 인수로 처리하지 않는다.
- 추가 전 전체 CPU·native dummy 검사 통과. 추가 후에는 종료 시각 요청에 따라 조작·회피·반격·Pause/R·화면 집중 검사만 수행했다.
- Computer-Use 미사용 요청을 따랐다. 실제 키/IME/DPI·장치 성능, 연꽃 양산은 미검증이다. F2 이동 광원/Bloom dummy p95 22.01/24.70ms로 목표 미달이다.
