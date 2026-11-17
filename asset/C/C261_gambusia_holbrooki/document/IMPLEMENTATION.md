# 첨부 외관 반영 · r03

사용자의 첨부 이미지를 최종 외관 기준으로 삼았다. 원시 입력은 `../imagegen/user_appearance_target.png`다. 수정 범위는 C261의 GPT Image 텍스처, 눈·아가미 조형, Sprite 출력 명암, 이에 종속된 2D 패스·미리보기·런타임 번들이다.

## 외형과 출력

내장 GPT Image로 암수 공통 UV 배치의 pigment를 생성했다. 올리브 등과 밝은 아이보리 배, 큰 색 덩어리, 얇은 지느러미 선·점을 사용한다. 원시 1254² PNG를 보존하고 Blender Image.scale로 1024² 작업 텍스처에 수용했다. sRGB 픽셀 샘플 비교에서 이중 감마 변환이 없음을 확인했다. GPT Image가 2,304프레임을 각각 생성한 것은 아니다.

눈 반경은 SL 비율 (0.038,0.014,0.040)에서 (0.050,0.024,0.047)로 변경했다. 아가미 덮개의 안쪽 법선을 바깥쪽으로 바로잡고 중앙 두께와 테두리 선을 보강했다. 덮개 UV를 밝은 배색 영역 쪽으로 조정했다. 리그·본·Action 수·동작 시간표는 유지한다.

Sprite는 카메라 공간 정규화 광원 (0.10,-0.35,0.93), 몸 wrap 0.25 / fin wrap 2.0을 사용한다. 내적은 `(N·L+wrap)/(1+wrap)`으로 계산한다. 기존 0.14/0.42/0.72 경계와 4단 선형 RGB 배율, sRGB 변환 후 가중 최근접 13색 양자화, 2px 외곽선은 유지한다. 눈 반사점은 UV 고정 (243,241,230), 별도 Emissive 강도는 0.12다. 변경 근거는 첨부의 밝은 볼·배와 어두운 등 대비이며 AssetPipeLine §8의 종별 변경 기록에 해당한다.

Base는 조명 없는 pigment다. Normal/AO/ORM/Emissive/Depth/WaterMask는 수정 모델에서 다시 계산했다. 데이터 패스에 Sprite 명암을 굽지 않는다. Alpha를 모두 동일하다고 주장하지 않는다. 눈 크기와 아가미 조형 변경은 관련 데이터·가림에도 반영된다.

암컷 640², 수컷 384², 밀도 71.910112px/BU, SL 6배/3.5배, 16행동·3구간·4시점·8패스, 셀별 3/12/3 샘플을 유지한다. 기본 게임 표시를 Sprite로 변경했으며 L로 기존 물리 재조명을 선택할 수 있다.

## 원본 보존과 검증

`../3D/versions/gambusia-r01.7z`에 원본 전체를 보존했다. 별도 폴더 복원 후 5,362파일의 SHA256을 확인했다. `restore_map.json`은 복원 경로·원본 ledger·archive SHA·현재 native source SHA를 기록한다. 배포기는 현재 파일 해시가 원본 ledger와 같은지 먼저 검사하고, 검증된 archive를 설치한 뒤 새 파일을 교체한다.

검증 근거:

- `../3D/saved_validation.json`: 저장본 96 Actions, 암수 각 816자세, 26본, UV/웨이트, 공유 경계·루프·임의 seek, 아가미 법선 방향.
- `../2D/gambusia-r03/package_validation.json`: 2,304셀·8패스, 프레임 여백, Normal 단위 길이, 동일 native source SHA.
- `sprite_revision_validation.json`: 몸 팔레트·외곽선, 피벗·카메라·SL 마커·시간표 유지, 패스별 실제 변경 픽셀 수.
- `runtime_validation.json`: 물리·이벤트·seek·실패 경로, 잘못된 manifest·손상 bundle 거부, C011 재조명 수치 비교, SDL dummy 성능.
- `gameplay_validation.json`: 기존 톡토기 capsule hit, pause/F2 정지, 전체 연못 루프의 SDL dummy 성능.
- `preview_validation.json`: Node 기반 HTML 제어 로직·파일 참조 검사. 실제 브라우저 검사는 아님.
- `relocation_validation.json`: 배포 경로에서 native 재개방, packed/external 이미지 및 6개 내장 도구 일치.

최종 수치와 한계는 `acceptance_summary.json`을 따른다. 실제 브라우저/GPU는 미검증이며 Pico2D 연결은 이번 수정 범위에 포함하지 않았다. 첨부의 픽셀 단위 복제는 아니며 native 셀 크기·팔레트·3D 모션 정합에 맞춘 외관이다.

## 재생성

현재 build_fish.py로 모델을 재구축한다. export_fish.py를 암수 × left/right/front/top의 8조합으로 실행하고 package_fish.py, verify_sprite_revision.py <복원 r01 루트>, build_review.py <프로젝트 루트>, compare_lighting.py <프로젝트 루트> 순서로 출력·검증한다. 기존 r01 모델에 색만 덧씌우면 이번 눈·아가미 수정은 복원되지 않는다.
