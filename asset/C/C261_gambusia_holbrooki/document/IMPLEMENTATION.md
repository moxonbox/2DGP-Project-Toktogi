# 구현·검수 기록 · 2026-11-17

기준은 AssetPipeLine v2.3, AssetSize v1.1 및 이 폴더의 기존 생물/모델/동작 명세다. 기존 명세 3개는 변경하지 않았다. 원본 해시와 생성 출처는 `source_contract.json`, 실제 배포 파일 해시는 루트 `delivery_manifest.json`에 둔다. 모든 문서 링크는 해당 파일 기준, 계약 JSON의 자산 경로는 C261 루트 기준이다.

## 시트 대응

GPT Image 암수 시트·프롬프트를 `sheet/`에 보존했다. C011 원본 스타일과 기존 Blender 6면을 참조했다. 모델은 시트를 기반으로 재구성한 편집 가능한 메시이며 이미지에서 3D를 완전히 역복원했다는 뜻이 아니다. 가려진 관절과 암수 지느러미 부착은 종별 명세로 보완했다. 외부 생물 사진은 복제/배포하지 않았다.

`comparison/model_detail_before_after.png`는 실제 native 렌더 전후다. 눈을 몸에 붙이고 돌출 입/아가미 판을 줄였다. 둥근 배·뒤쪽 등지느러미·독립 꼬리 팬·읽히는 가슴지느러미·전방 작은 배지느러미·고정 fin ray/점무늬를 반영했다. 수컷 gonopodium은 별도 보존했다. 과장된 몸 비율은 생성 시트/게임 스타일이며 생물 비례 측정값으로 사용하지 않는다.

## 모델·출력

`3D/saved_validation.json`: 저장본 재개방, 암수 각 816자세, 26본, 7지느러미, 눈 2개, 정규화 웨이트, 무할당 정점 0, SL·UV 범위·임의 seek·루프·행동 경계 검증. 공유 경계 오차 < 2e-16BU, seek 오차 0. 원본 hash는 `bbd850e5cea27549cce2b218663dc9e030a70684916af9c4e91ce5ccf8384ecc`.

UV checker와 부품별 수치는 `comparison/*_uv_checker.png`, `comparison/uv_validation.json`. 지느러미 앞뒤는 동일 차트를 사용한다. 얇은 가장자리, 아가미 홈의 단색 texel, 숨은 몸/턱 캡은 의도적으로 UV 면적이 0이다. 이 부위에 고해상도 무늬를 그릴 수 있는 전면 고유 unwrap은 제공하지 않는다. 몸–지느러미·아가미·턱 힌지 겹침은 접합이다. 임의 모든 부품쌍의 무관통 판정은 하지 않았다.

2,304개의 개별 PNG는 `2D/<family>/<sex_action_phase>/<view>/<index>.png`다. 각 셀은 Sprite/Base/Normal/AO/ORM/Emissive/Depth/WaterMask의 8패스를 세로 적층한다. 아틀라스는 `2D/gambusia-r01/<sex>_<action>_<view>_<pass>.png`, 표본·시간·bbox·피벗·mouth_tip/body_ref/attack_socket/SL 마커는 manifest에 있다. 4시점 전체 최소 여백 23px, Normal 길이 오차 최대 0.00670. `package_validation.json`, `validation_<sex>_<view>.json` 참조.

Base는 조명 없는 sRGB, Normal·ORM·Depth·Emissive는 선형 수치다. Normal/데이터 A=255를 coverage로 쓰지 않고 Base.A로 마스킹한다. ORM은 **R=AO/G=roughness/B=metallic**이며 C011의 RM과 배열이 다르다. 지느러미 alpha .84, 외곽선 #22313B·2px, C011 4단 명암·몸 전용 olive/silver 13색 팔레트를 사용한다. 선형 bilinear UV 보간 후 sRGB/팔레트, 화면은 Nearest다. 눈은 검은 Base와 별도 UV 고정 발광을 갖는다.

투명 지느러미는 가장 가까운 투명층과 뒤 불투명층을 합성하는 근사다. 여러 반투명 지느러미가 중첩될 때 완전한 다층 광학은 재현하지 않는다. AO는 5방향 정점 가시성 근사이며 별도 패스다. 런타임 C011 BRDF의 동등 비교에서는 AO를 다시 곱하지 않는다. UV 하이라이트는 장식이고 광원 반사와 구분한다. Bloom은 구현 범위에 포함하지 않았다.

## 동작·효과

16행동마다 pre/mid/end, 총 암수 96 Action을 저장했다. hover/cruise/forage/gape의 mid는 루프다. 표본은 중복 마지막 셀 없이 pre/end 3개, mid 12개다. 제작 포즈와 120Hz 게임 시간은 분리된다. 속도/회전/피격 가중치 함수는 `runtime/motion_spec.py`에서 3D 제작에 사용할 수 있다. 현재 PNG 런타임은 기본 가중치의 출력 클립을 선택하며 임의 본 가중치 혼합이나 두 PNG의 알파 중첩을 관절 보간으로 제공하지 않는다. 방향 전환은 지원 좌우 뷰 선택 방식이다.

물리 root만 이동/중력을 소유한다. 몸 전체 이탈과 mouth_tip 노출을 구분하고, 실제 변형 메시 삼각형과 물 평면을 교차시킨다. 표층에서는 몸 중심과 97% 이상 몸 정점이 잠기며 입끝만 노출한다. 화면 가림은 Depth의 world Z와 물리 root로 계산한다. 배경 수면선은 사선 카메라의 입 깊이 단면을 투영한다. VFX에는 메시 교차점의 카메라 깊이 보정을 적용한다. 정적인 WaterMask는 진단용이며 게임 물높이 판정을 대신하지 않는다.

포획은 현재 활성구간·거리·대상·공격 ID를 모두 만족할 때 1회다. 삼킴은 같은 cycle에서 실제 포획한 자원만 1회 반영한다. gape/돌파는 무피해다. 플레이어 접촉은 C011 capsule에서 확인하고 기존 Game.hit()를 호출한다. 체력 시스템을 새로 만들지 않았고 HP 수치는 미정이다.

돌파 속도 3.6SL/s, 중력 3SL/s² 등은 명시적 게임 튜닝값이다. 종의 실제 도약 능력·호흡 습성 측정값이 아니다. 공중에서는 추진이 꺼지고 실제 물 교차 때만 물튀김/파문이 각각 1회 발생한다. 수역 미도달은 중력/실패로 남으며 텔레포트하지 않는다. seek는 검사 전용이며 이벤트를 실행하지 않는다. 저장 상태에는 세대·phase·cycle·공격 ID·확정 효과를 포함한다.

| 요구 | 검증한 결과 | 근거 |
|---|---|---|
| GH-MOV-01 | 실제 이동·무리 간격·turn 종료 방향, 리그 파동 | runtime_validation.json, saved_validation.json |
| GH-MOV-02 | 근접 포획/삼킴 각 1회, 원거리 둘 다 0회 | runtime_validation.json |
| GH-MOV-03 | 기본 돌파 비활성, 공중 추진 없음, 예기치 않은 수역 이탈 중력 | runtime_validation.json |
| GH-MOV-04 | 암수 SL 5.792376/3.378886BU, 정확한 G. holbrooki | source_contract.json, saved_validation.json |
| GH-MOV-05 | 4시점 패스 정합, C011 BRDF 최대 1/255 채널 차이, 재질 음성 대조 | runtime_validation.json, ../comparison/material_negative_controls.png |
| GH-MOV-06 | 상승→입 노출→gape 2회→잠수, 몸 수중·공격/섭식 0회 | runtime_validation.json, ../previews/female_surface.png |
| GH-MOV-07 | 출수→정점→낙하→실제 재입수, splash/ripple 각 1회 | runtime_validation.json, ../previews/female_breach.png |
| GH-MOV-08 | 취소/공중 취소/미도달/일시정지/seek/저장복원 중복 없음, 10/15/20/30/60fps 결과 일치 | runtime_validation.json, ../previews/replay_traces.json |

이 표는 코드·저장본·오프라인/SDL 소프트웨어 검증의 범위다. 실제 브라우저 조작·표시 GPU·Pico2D를 통과했다는 뜻이 아니다. 포식 자료의 Sminthurides sp.를 S. aquaticus로 바꾸지 않았고 구애·공동 입력·태생/새끼 시스템을 추가하지 않았다.

## 로더·성능·인계

ZIP·잠금·manifest schema/revision/기반 서명/원본 및 payload hash를 검증한다. 전체 3,714 payload의 checksum은 `bundle_validation.json`. 중복 키/셀, 누락 패스·뷰·표본, 비유한 마커·피벗, 시간·rect·전환 오류는 숨기지 않고 실패시킨다. 15가지 오류 입력 검사와 손상 archive 확인을 기록했다. HTML은 동작 코드/로컬 파일·범위 검사를 거쳤으며 브라우저 GUI는 열지 않았다.

원본 RGBA 전량은 20,535,312,384byte다. ZIP 약 727MB를 메모리 상주량으로 오인하지 않는다. 개별 셀 4개, 준비된 필드 24개, 최종 셰이딩 이미지 24개를 제한 캐시한다. revision·셀·뷰를 포함한 파일키·광원·재질 모드·Normal·발광·물높이 키를 분리했다. geometry NPZ는 암수별 지연 로드한다. 총 working set 예산은 512MiB이며 프로세스 private commit은 별도로 기록한다.

`runtime_validation.json`은 로드/워밍업과 이동 광원 120프레임의 CPU 계산·RGBA 전송·SDL dummy blit를 구분한다. `gameplay_validation.json`은 C011까지 포함한 워밍업된 연못 idle 120프레임과 실제 player capsule 접촉을 기록한다. 성능은 해당 측정 환경/로그 수치를 따른다. 다른 장치·실제 창·GPU 업로드 성능은 미검증이다. `preview_validation.json`은 Node의 mocked DOM/canvas 검사이며 실제 브라우저 판정으로 사용하지 않는다.

Blender MCP는 연결되지 않아 Blender 5.3.0 headless CLI로 제작·재개방·출력했다. Computer-Use는 사용하지 않았다. Pico2D/DEC-06 다방향 양산·F2 Normal/Bloom은 별도 보류 대상이다. 현재 선택 실행본의 기본 렌더러는 Pygame이며 기존 기본 게임 소스/번들을 덮어쓰지 않는다.

`3D/versions/restore_map.json`에 시트 수정 전 작업 초안과 마지막 자동 저장본의 7z 복원 경로·hash를 기록한다. 기존 C261에는 명세 3개만 있었으므로 이 archive는 이전 배포판이 아닌 작업 중 초안이다. 복원은 별도 폴더에 압축을 풀고 hash를 확인한 다음 비교한다.

재현 순서: Blender로 `3D/tools/build_fish.py` → 최종 blend로 `export_fish.py -- <sex> <view>` 8조합 → Python `package_fish.py` → `verify_runtime.py` → `build_review.py <project>` 및 `compare_lighting.py <project>` → Node `verify_preview.js`. export worker JSON은 `.json.gz`로 보존했고 패커는 이를 읽을 수 있다. 원본 .blend를 재생성하면 해시가 바뀌므로 모든 패스를 다시 출력해야 한다.

최종 측정 판정: 기능/원본/패킹 검사는 통과. 이동 광원은 p95 18.55ms·최대 20.23ms로 16.7ms 예산을 초과하여 성능 관문은 보류한다. 워밍업된 연못 idle은 p95 8.34ms·최대 9.28ms다. 각각 단일 측정의 CPU/SDL 소프트웨어 결과이며 GPU 60fps 보장은 아니다.
