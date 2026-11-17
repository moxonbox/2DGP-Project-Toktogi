톡토기 통합 보완본 integrated-r5

Blender Text Editor에서 SET_PLAYABLE_CLIP.py의 CLIP과 VIEW를 설정해 실행합니다.
r5 플레이어 클립 63개, 지면 관찰 클립 18개, 손질 연결 클립 1개가 들어 있습니다.
관찰 동작과 obs_antenna_to_furca는 left 뷰를 사용합니다. 각 플레이어 클립은 supported_views를 따릅니다.
수면·산란은 제외했습니다.

playable_manifest.json에서 samples[].views[view].rect로 128×128 셀을 읽습니다.
피벗은 왼쪽 위 기준 (64,88)이며 필터는 Nearest입니다. 카메라와 직교 배율 1.78을 공유합니다.
Sprite는 표시용입니다. 재조명 시 Base A로 Normal/RM/Emissive를 마스킹합니다.
r5의 right 호환 뷰와 yaw_180은 별개의 뷰입니다. 관찰용 obs_jump는 그림에 수직 이동이 포함됩니다.

transition_antenna_furca.png는 앞발을 든 채 06에서 연결 Action을 거쳐 07로 이어집니다.
이 경로의 셀 시작·종료와 경계 홀드 소유권은 visual_bindings.groom_chain에 기록했습니다. 샘플 인덱스는 0부터 셉니다.
transition_carry_dance.png는 두 개체와 집게가 함께 이어지는 19→20 프리뷰입니다.
각 독립 클립은 previews 폴더에서 128px APNG로 볼 수 있습니다.
06의 120ms 누름 홀드는 2D 표시 시간표에 들어 있습니다.

geometry_validation.json은 교차 후보와 접촉 간극, 가시 픽셀, 장면 여백을 기록합니다.
pose_validation.json은 선택기와 r5 마커, runtime_validation.json은 128px 셀·시간·전환 검사입니다.
시각 검증 범위는 오프라인 출력과 Pygame 재생입니다. 실제 게임 입력·물리 연결은 게임 구현에서 검증합니다.

06의 12·18번 누름에서 작업발과 더듬이가 닿아 보이는 픽셀 주변의 명암을 Sprite에 보강했습니다.
07의 f82.25와 f112–115를 보정했습니다. 일부 복귀 교차는 geometry_validation.json에 남아 있습니다.
08의 21·22번 출력은 유지하고 Blender의 접촉·이탈 사이 경로를 수정했습니다.
