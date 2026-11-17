# Pico2D 백엔드·좌표·자원 계약

2026-11-17 · v1.1 · **재구현 설계 / 실기 미검증**. [Rebuild](Rebuild.md)의 출력·입력 어댑터 상세이며 게임 규칙은 포함하지 않는다.
고정 후보는 [Pico2D 1.5.1](https://pypi.org/project/pico2d/1.5.1/)이다. wheel SHA256은 `3514bca996d7a8b77f21ba1967fe119982a0d9aa37fc40966ea94b4b39789fd3`; 실제 설치본·PySDL2·DLL의 호환 검증은 별도다.

## 1. 책임과 연결

- `pico_backend.py`는 창·renderer 접근, RGBA 업로드, 좌표·clip·도형·폰트 출력, 이벤트 수집과 자원 해제를 맡는다. Game·Course·physics·Timeline·MotionSet은 Pico2D/SDL을 import하지 않는다.
- `input_clock.py`가 SDL 이벤트를 [Control](Control.md)의 엔진 독립 입력으로 변환한다. `materials.py`는 검증된 Pillow 맵, `sprite_renderer.py`는 최종 CPU RGBA와 표시 메타데이터를 제공한다.
- 게임 위치·충돌·효과는 읽기만 한다. 출력 FPS·이미지 크기·광원 변경이 시뮬레이션 상태를 수정하지 않는다.
- Pico2D `open_canvas`, `hide_lattice`, `Image.draw/draw_to_origin`, `load_font`, `update_canvas`, `close_canvas`를 실제로 사용한다. 별도 Pygame 창·별도 SDL renderer·GPU BRDF 경로로 대체하지 않는다.

## 2. 환경·초기화

- Windows x64에서 Python·pico2d·Pillow·PySDL2·PySDL2-DLL의 정확한 버전·해시와 SDL2/SDL_image/SDL_ttf/SDL_mixer의 실제 로드 경로를 기록한다. 다른 설치본의 DLL을 혼합하지 않는다.
- `pico2d.pico2d`의 renderer는 창 생성 후 조회한다. `from ... import renderer`의 오래된 핸들에 의존하지 않으며 포인터의 실제 유효성·SDL 주 버전·필수 함수 지원을 검사한다. 1.5.1 내부의 `is None` 비교만으로 ctypes NULL 검사가 충분하다고 가정하지 않는다.
- 창은 1280×744, 논리 필드는 960×560이다. 초기 격자를 숨기고 캡션을 설정한다. 앱 초기화가 끝나기 전 기본 격자/빈 프레임이 노출되는지도 환경 관문에서 확인한다.
- Pico2D의 `clear_canvas()`는 고정색을 사용하므로 매 표시 프레임의 지우기는 같은 renderer에 현행 PLAY_CLEAR=(99,108,112)를 지정해 수행한다. F2는 자체 배경을 사용한다.
- Pico2D 1.5.1은 오디오도 초기화한다. 신규 음악·효과음은 범위 밖이며 오디오 장치 실패와 필수 영상·폰트 초기화 실패를 구분한다. 실패 단계·SDL 오류를 기록하고 부분 자원을 회수한다.
- 단조 증가 고해상도 시계로 dt를 측정한다. 60fps 제한과 vsync 대기를 중복 적용하지 않으며 실제 renderer·동기화 설정을 성능 기록에 남긴다.
- 가상환경·폰트/DLL 탐색은 실행 파일 기준 경로를 사용한다. 임의 cwd·한글/공백 경로와 누락 파일을 검사하고 설치 패키지 내부를 현장에서 수정하지 않는다.
- 1.5.1 open_canvas는 내부에서 clear/present를 두 번 실행한다. 열기 전에 격자를 끄더라도 고정 기본색 노출은 별도로 검사한다. 첫 정상 프레임은 지정 지우기 색으로 그린다.
- open_canvas 내부의 초기화 반환값 누락·창/renderer 실패는 호출 후 검사만으로 보호되지 않는다. 사전 의존 검사와 단계별 실패 주입으로 안전 종료를 증명하고, 필요한 고정 버전 어댑터 보완은 소스/라이선스와 함께 관리한다. 해결 전에는 R-02를 통과시키지 않는다.

<a id="backend-coordinates"></a>
## 3. 좌표·DPI·클리핑

- 내부 논리 좌표는 좌상단 원점, +x 오른쪽·+y 아래다. 필드 오프셋은 (160,92), C011 피벗은 (64,88)이다. 배율 s의 목적 좌상단은 `필드 원점+월드 위치−Camera−피벗×s`다. 기존 코스 Camera는 (0,0)이다.
- 목적 사각형 `(x,y,w,h)`는 Pico2D `draw_to_origin(x,H−y−h,w,h)`로 출력한다. H는 선언된 논리 캔버스 높이다. 한 번의 변환을 Sprite·마커·글자·도형에 일관되게 적용한다.
- 게임 물리의 실수 위치와 픽셀 출력의 정수 반올림을 분리한다. 현행 `round` 위치·피벗과 1px 경계 표본을 대조하며 이동마다 정수 물리 좌표로 덮어쓰지 않는다.
- SDL 창 크기와 [renderer 출력 크기](https://wiki.libsdl.org/SDL2/SDL_GetRendererOutputSize)를 따로 읽는다. OS DPI가 다르면 viewport/scale과 역변환을 명시하고 클릭·광원·clip에 같은 매핑을 사용한다.
- 기본 고정 창은 유지한다. 불가피한 letterbox 여백은 입력 대상에서 제외하고 논리 필드나 에셋의 몸 크기를 임의 변경하지 않는다. 프리뷰 1×/2×/3×는 논리 픽셀의 정수 배율이다.
- [SDL clip rect](https://wiki.libsdl.org/SDL2/SDL_RenderSetClipRect)는 viewport 기준 좌상단 좌표다. Pico2D의 하단 원점 변환을 다시 적용하지 않는다. 변경 전 clip 활성 여부·사각형을 보존하고 예외 경로에서도 복원한다.
- Normal은 카메라 R 오른쪽·G 위·B 카메라 방향이다. 이미지 행이나 API y축이 달라도 G를 임의 반전하지 않는다. `right`와 `yaw_180`을 구분하며 제작된 방향을 미러·화면 회전으로 대체하지 않는다.
- [StageLevel](StageLevel.md)의 Camera는 평행 이동만 한다. 월드 광원과 객체에 같은 이동을 적용하고 카메라 추적을 리그 yaw·Normal 회전으로 해석하지 않는다.
- 화면 밖 객체의 그리기 생략과 물리/작업 중단을 분리한다. 경계 양쪽의 객체·그림자·마커를 같은 viewport와 순서로 그리고 Level별 화면 원점으로 재설정하지 않는다.

## 4. RGBA·텍스처 업로드

- 입력은 top-down 행 순서의 연속 RGBA8, 크기와 byte 수가 일치하는 버퍼다. `SDL_PIXELFORMAT_RGBA32`로 생성하고 실제 형식·크기·접근 모드를 확인한다.
- 동적 출력은 streaming texture를 재사용한다. [SDL_LockTexture](https://wiki.libsdl.org/SDL2/SDL_LockTexture)의 반환 pitch로 행마다 `width×4`byte를 복사하고 매 lock 영역의 모든 픽셀을 초기화한 뒤 unlock한다.
- 잠긴 버퍼의 이전 내용은 보존된다고 가정하지 않는다. lock 실패 시 쓰지 않으며 성공 후 예외에서도 unlock한다. 입력 버퍼는 복사가 끝날 때까지 유효해야 한다.
- width/height·stride·buffer 길이·셀 최대 예산을 업로드 전에 검증한다. `pitch < width×4`, 음수/비유한 크기, NULL 포인터는 복사하지 않고 오류로 처리한다.
- 같은 renderer의 텍스처를 Pico2D Image로 감싼다. 업로드 전에 기존 프레임의 Image가 참조 중인 텍스처를 파괴하지 않으며 프레임마다 PNG 저장·재로드를 하지 않는다.
- 텍스처의 [ScaleMode](https://wiki.libsdl.org/SDL2/SDL_SetTextureScaleMode)를 Nearest로 지정하고 실제 지원값을 확인한다. 1px 체크 패턴과 1×/2×/3× 결과로 선형 필터·번짐을 검출한다.
- Sprite는 straight Alpha, Base는 표면 coverage다. Normal/RM/Emissive 미리보기는 Base coverage를 적용하며 다섯 패스의 Alpha를 일괄 같게 만들지 않는다.
- Sprite 합성은 기존 알파 규약을 유지한다. 불투명 CPU 프리뷰를 통째로 올릴 때는 이중 알파 합성을 방지하고 텍스처 blend/color/alpha modulation의 설정 누출을 검사한다.
- 패킹·파일 검증과 source lock은 [제작 파이프라인](AssetPipeLine.md)이 기준이다. 전송 채널 순서·행 뒤집힘은 빨강/파랑·위/아래·반투명 모서리 표본으로 검사한다.

## 5. 재질·후처리·도형

- `lighting.py`의 CPU 수식과 [2Dshader](2Dshader.md)를 재사용한다. RGB 기준 대조를 마친 뒤 원본/평탄 Normal·Emissive·Bloom을 추가하며 각 변경을 개별 비교한다.
- 실시간 광원에는 객체별 로컬 벡터를 전달한다. C011 플레이의 power=.82·ambient=.34, 기존 감쇠·거칠기 하한·접점 잉크·윤곽과 Sprite Alpha를 유지한다.
- Bloom은 F2 실시간 조명 프리뷰에만 적용한다. 발광 전용 입력·선형 RGB 합성·타일 밖 6px 여유는 셰이더 명세를 따르며 피벗·충돌·Sprite Alpha는 바꾸지 않는다.
- Bloom의 배경은 실제 프리뷰와 같은 CPU 합성 버퍼로 확보한다. 단순히 SDL 기본 가산으로 바꾸거나 감마 RGB에서 더하지 않는다. UI·마커는 합성 뒤 그리고 매 프레임 GPU readback을 기본 경로로 삼지 않는다.
- Pygame 도형으로 만든 발판·먹이·씨앗·가시·그림자·F2 패널도 이식 대상이다. 정적 도형은 캐시 이미지, 동적 도형은 같은 SDL renderer/CPU 버퍼로 표현하고 위치·alpha·그리기 순서를 대조한다.
- 표면 비교·Bloom 결과가 없는 셀·전부 검은 발광·꺼진 토글은 원래 출력을 그대로 유지한다. 확대·clip·후처리 여유가 마커 위치를 바꾸면 실패다.
- 평탄 Normal 비교는 디코딩 후 정확한 (0,0,1)을 사용한다. 원본 맵의 UNORM 양자화값 (128,128,255)을 단순 교체해 약한 기울기를 남기지 않는다.

## 6. 한글 폰트와 입력

- Pico2D load_font에 실제 폰트 파일을 전달한다. 한글·숫자·방향키 글리프를 검사하고 OS 폰트 경로 및 대체 폰트 정책을 기록한다. 폰트 동봉 시 재배포 권한도 확인한다.
- 현행 좌상단 텍스트 배치와 Pico2D Font.draw의 수직 기준은 다르므로 글리프 높이로 보정한다. 버튼·검색칸의 글자가 잘리거나 hit-test 영역과 어긋나지 않게 한다.
- 1.5.1의 Font.draw는 호출마다 표면·텍스처를 만든다. 반복 라벨은 폰트/크기/문자열/색을 키로 제한 캐시하고 텍스트 변경 시 갱신한다. 캐시가 끝없이 늘어나지 않게 한다.
- 한글 검색의 조합 문자열·확정 문자열을 별도로 그린다. 텍스트 입력 사각형은 DPI/좌표 변환 뒤 지정하며 포커스 상실·장면 종료 때 조합 상태를 정리한다.
- [SDL_PollEvent](https://wiki.libsdl.org/SDL2/SDL_PollEvent)는 창을 만든 스레드에서 큐를 한 번 소비한다. PySDL2의 실제 SDL_Event 구조를 쓰며 기존 Pygame DLL 위치·수동 ABI 배열을 복사하지 않는다.
- Pico2D get_events의 축약 Event를 사용하지 않는다. [키 이벤트](https://wiki.libsdl.org/SDL2/SDL_KeyboardEvent)의 timestamp·repeat·keysym/scancode/mod와 포커스·TEXTINPUT/TEXTEDITING·마우스·휠·종료를 원시 SDL_Event에서 변환한다. 내용·소비·시간 정책은 [Control](Control.md#atlas-controls)을 따른다.
- 프레임 시계와 SDL timestamp의 기준점을 시작 시 맞추고 순환을 펼친다. 테스트용 시각과 입력을 주입할 수 있게 하며 OS 절전/지연 뒤 처리하지 않은 시뮬레이션 시간을 조용히 버리지 않는다.

## 7. 소유권·종료·오류

- Pico2D 1.5.1 Image.__del__은 texture를 직접 해제한다. 백엔드 관리 Image의 명시적 close와 destructor를 멱등하게 맞춰 하나의 소유자만 한 번 해제하고 renderer 파괴 후 접근을 막는다.
- Font에는 자동 close를 가정하지 않는다. 소유한 폰트에 [TTF_CloseFont](https://wiki.libsdl.org/SDL2_ttf/TTF_CloseFont)를 한 번 호출하고 핸들을 비운 뒤 TTF_Quit가 실행되게 한다.
- 정상·창 닫기·초기화 실패·렌더 예외 모두 `try/finally` 정리 경로를 탄다. 텍스트 입력 중지, Assets ZIP/캐시, 텍스처·폰트, 마지막으로 Pico2D canvas 순서로 정리한다.
- 이미 해제한 자원은 재사용하지 않으며 생성 중 실패한 NULL 객체도 안전하게 정리한다. 오류는 파일/셀·함수·renderer·DLL 정보를 포함하고 빈 화면 성공으로 숨기지 않는다.
- renderer/device reset 시 이전 텍스처를 계속 쓰지 않는다. 보존 CPU 데이터에서 재생성하거나 명확히 종료하는 지원 정책을 정하고 검증한다.
- App 종료·초기화 실패의 close를 여러 번 호출해도 안전해야 한다. 자원 생성/해제 수와 남은 참조를 진단 가능하게 하고 texture·font를 해제한 뒤 Python destructor가 재해제하지 않게 한다.

## 8. 캐시·성능·인수

- 캐시는 맵·조명 RGBA·텍스처·글자·Bloom을 구별한다. 관련 키는 asset/revision·셀·광원·주변광·물성·발광·Normal/Bloom 설정이며 원본과 조명 결과의 수명을 섞지 않는다.
- 디코딩 메모리의 시작값은 고유 셀×5×128×128×4byte다. 셰이딩·텍스처·텍스트·후처리 복사와 캐시 상한을 더해 기록하며 압축 ZIP 크기로 대체하지 않는다.
- C011 2,374셀의 5패스 RGBA 전체는 약 741.9MiB다. 두 Level 선행 준비가 전 셀 상주를 뜻하지 않으며 경계에서 필요한 포즈/맵만 예산 안에서 준비한다.
- 현행 맵 36셀·표면 계산 24셀·조명 96셀·글자 512항목은 초기 비교 상한이다. 새 Texture/Bloom 캐시 상한은 측정해 정하고 재생·검색·레벨 왕복 시 메모리 증가를 기록한다.
- B-01: 단일 창/renderer·Pico2D Image 출력·한글 폰트·기본색·격자 숨김·종료를 확인한다. 입력·출력 핸들이 같은 SDL 라이브러리를 사용하는지 기록한다.
- B-02: 채널/행/반투명 가장자리·pitch·Nearest·1px 피벗·DPI/clip·작업 마커를 검사한다. CPU Alpha 차이 0·RGB 최대 1/255 기준과 SDL 최종 합성 오차를 따로 보고한다.
- B-03: 고정 포즈에서 광원/Normal/Emissive/Bloom을 한 변수씩 바꾸고 결과·음성 대조·프리뷰 밖 누출을 검사한다. 토글 복귀 시 기준 픽셀로 돌아와야 한다.
- B-04: 반복 F2/플레이 전환·검색·재생·종료, 부분 실패·업로드 실패·renderer reset에서 중복 해제와 자원 증가를 확인한다.
- B-05: 기준 장치에서 로딩/워밍업, 120프레임 p95/최대·CPU 계산/업로드/합성·캐시 크기를 기록한다. 의도적 vsync/제한 대기와 처리 비용을 분리하고 p95 목표·최대 지연 허용값·메모리 상한을 시험 전에 정한다. 60fps 처리 목표 16.7ms 미달은 실기 인수 미완료다.
- 자동 RGBA 검사는 SDL 창 없이, 실제 업로드·폰트·입력·DPI 검사는 실기에서 수행한다. 과거 Pygame PASS를 새 백엔드의 합격 증거로 재사용하지 않는다.
- SDL 합성은 고정 배경의 채널/반투명 표본에서 CPU 기대 합성과 RGB 채널 오차 최대 1/255를 대조한다. 글자는 래스터 차이와 글리프·크기·배치/잘림 검사를 구분한다.

## 9. 연속 Level의 출력 수명

- Level 변경에 renderer·Assets·공용 텍스처를 파괴하지 않는다. 객체 배치는 월드 키, 재질 맵은 asset/revision 키를 사용한다. 경계 워밍업·추가 I/O는 StageLevel S-06에서 측정한다.
- 두 Level의 공용 캐릭터·재질은 같은 캐시를 쓰며 광원·물성·배율을 재초기화하지 않는다. 데이터 준비 실패 시 마지막 정상 출력과 오류 원인을 보존한다.

## 10. 근거와 적용 한계

- 1.5.1 wheel의 `pico2d.py`·METADATA와 공식 SDL 문서를 대조했다. 내부 renderer 접근·Image 해제·Font 출력 방식은 고정 버전 의존이며 라이브러리 갱신 시 재검수한다.
- 이번 작업은 명세 작성이다. 실제 장치·한글 IME·DLL 조합·성능은 미검증이며 소스·폰트·의존성 잠금은 구현 관문에서 확정한다.
