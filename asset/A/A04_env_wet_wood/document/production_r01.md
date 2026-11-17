# A04 젖은 가지 — environment-r01 제작 기록

2026-11-17. 정적 제작 후보를 구현·파일 검증했다. 게임 연결·물리 검증과 DEC-06 양산 승인은 완료하지 않았다.

## 채택 범위와 출처

고정된 젖은 가지를 채택했다. 몸체·분지·마디·밝은 절단면이 편집 가능한 메시다. 분지는 몸체에 겹쳐 접합하며 내부 면을 삭제하지 않았다. 이 겹침은 정적 소품의 의도한 접합이다. 부유형과 고정형을 혼합하지 않는다.

- 원본 [외형 명세](env_wet_wood_model.md)·[동작 명세](env_wet_wood_movement.md)·[생태 자료](env_wet_wood.md)는 수정하지 않았다.
- 공통 기준은 [AssetPipeLine v2.3](../../../../document/markdown/AssetPipeLine.md), [AssetSize](../../../../document/markdown/AssetSize.md), [StageLevel](../../../../document/markdown/StageLevel.md), [Rebuild](../../../../document/markdown/Rebuild.md)다.
- [기계 판독 계약](production_contract_r01.json)에 폴더 ID·논리 ID·선택 크기·예산·카메라·재질을 분리했다. 미정인 8자리 번호를 발명하지 않고 `clip/view/000.png`와 manifest 키를 사용한다.

## 크기·색·표시 계약

- 선택 길이 5.0×C011, 목표 X 길이 4.826980 BU. 이는 상대 연출값이다. C011 몸 대용값 0.965396 BU와 카메라 환산 0.01390625 BU/px를 사용한다.
- 생물 길이 mm는 null이다. 모듈 크기를 생물 실측 또는 mm→BU 물리 단위 변환으로 해석하지 않는다.
- 출력 512×512px, 1× Nearest. game_left Sprite 실측 328×126px. 피벗과 3D 앵커의 투영 좌표는 뷰별 manifest에 있다. 모든 뷰의 Sprite/Base 투명 여백은 최소 8px다.
- 기준색 `#947861`, 거칠기 0.67, 금속성 0, 발광 0은 제작 선택값이다. 젖음은 지오메트리를 바꾸지 않는 고정 색/거칠기 마스크다. 실측 PBR로 주장하지 않는다.
- Sprite에는 C011의 네 단계 선형 명암과 자산별 색상 팔레트를 사용한다. 실제 palette_rgb는 뷰별 기록이다. Base는 조명·AO를 굽지 않는다. 디더·AA·mipmap·임의 trim·회전·미러는 사용하지 않는다.
- 외곽선은 C011과 같은 #22313B, dx²+dy²≤5 확장이다.
- 5패스 순서는 Sprite / Base / Normal / RM / Emissive다. Normal·RM·Emissive A=255, coverage는 Base A로 읽는다. AO 별도 베이크는 이번 범위에서 제외하며 소비자 기본값 1을 사용한다. RM B는 예약 0이다.
- Blender 미리보기에는 원본 C011의 AgX·조명 3개·World 설정을 복제했다. CPU Sprite 출력과 게임 연속 재조명은 별도 경로다. [공유 광원 비교판](../2D/environment-r01/shared_light_compare.png)은 기존 게임 lighting.py의 power .82·ambient .34를 사용한다.

## 저장·검증

- 삼각형 436, 본 0. 정적 환경에 불필요한 리그·Action·NLA를 만들지 않았다. 메시는 닫힌 편집용 형상을 유지한다.
- UV는 잎/패치의 XY, 경계면의 평면 투영, 돌의 분리된 섬을 사용한다. 밑면·측면의 반복은 의도적이다. UV 유한값과 저장 후 존재를 검사했다. 체크 타일로 늘어짐을 판정하는 별도 시각 검수는 미실행이다.
- .blend 재개방, 프레임 1/30/12/60/1의 평가 정점 해시 일치, packed 이미지와 외부 PNG 바이트 일치를 확인했다. 상대 이미지 경로를 사용한다.
- 7시점·7셀의 크기·경로·파일 해시·데이터 Alpha·Normal 길이·외접 범위·투명 RGB를 검사했다. 생물 사실 검증과 런타임 플레이 검증을 대신하지 않는다.
- [검수 결과](../../_pipeline_r01/validation.json), [저장본 결과](../../_pipeline_r01/saved_validation.json), [출처 해시](../../_pipeline_r01/source_evidence.json)를 참조한다.

## 보류

floating_bob은 현행 부력 제외 범위다. contact_reaction은 환경 이벤트 연결 후 제작한다.

현행 C011 로더는 128px 전용이므로 기존 실행 묶음을 교체하지 않았다. 신규 셀 크기 지원·상태/충돌 바인딩·실기 성능을 별도 검증해야 한다. 이 제작본의 `production_export_allowed`는 false다.
