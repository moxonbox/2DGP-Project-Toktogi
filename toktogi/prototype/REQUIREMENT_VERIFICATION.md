# v2.1 요구 추적 — framework-r4

[플레이 명세서](../document/markdown/022_toktogi_playable_action_animation_spec.md) §17의 72개 ID를 현재 실행본과 대조했다. 기존 미대조 14건을 현행 프로필 기준으로 다시 분류했다. 11건은 [추가 회귀](verify_requirements.py)로 현행 하위 사례를 확인했고, 3건은 현행 범위 밖이다. 아래 ID의 결과는 [verification.json](verification.json)의 requirement_trace에 있다. 하위 사례 확인은 해당 요구의 모든 변형을 통과했다는 의미가 아니다.

| 시험 | 상태 | 실행 결과 또는 남은 조건 |
|---|---|---|
| REV-MAT-01 | 하위 사례 확인 | `reference_shader_equivalence`. 24개 셰이더 기준 이미지. |
| REV-MAT-02 | 하위 사례 확인 | `reference_shader_equivalence`. 거칠기·금속성 기준 비교. |
| REV-HYB-01 | 현행 범위 밖 | 장식 배경·베이크 경계를 플레이에서 사용하지 않는다. 혼합 장면을 채택할 때 검사한다. |
| REV-HYB-02 | 현행 범위 밖 | 베이크 예외 자산별 광원 정책을 쓰는 활성 프로필이 없다. |
| REV-PXL-01 | 하위 사례 확인 | `q_both_support_sets_all_10hz_phases`. Q 양방향과 접지 세트의 저표시율 표본. |
| REV-VEL-01 | 하위 사례 확인 | `space_hold_preserves_walk_shift_brakes`. 정적 발판 속도 합산 및 Shift. |
| REV-BRAKE-01 | 하위 사례 확인 | `space_hold_preserves_walk_shift_brakes`. 정적 발판 제동. |
| REV-REC-01 | 하위 사례 확인 | `recovery_jump_uses_visible_landing`. 착지 표본 재도약. |
| REV-ELA-01 | 하위 사례 확인 | `elastic_pre_post_same_direction_aim`. 탄성 조준과 발사 방향. |
| REV-ELA-02 | 하위 사례 확인 | `timestamped_inputs_5_120fps`. 입력 창 안팎과 표시율. |
| REV-ELA-03 | 하위 사례 확인 | `timestamped_inputs_5_120fps`. 전달한 입력의 단일 발사. |
| REV-ELA-04 | 하위 사례 확인 | `elastic_pre_post_same_direction_aim`. 착지 전후 탄성 준비. |
| REV-CAP-01 | 하위 사례 확인 | `course_spawn_and_checkpoint_clearance`. 시작점·체크포인트의 고체 겹침 거절. |
| REV-FOOT-01 | 하위 사례 확인 | `ledge_q_direction_share_support_gate`. 양쪽 가장자리에서 반전 지지 검증. |
| REV-FOOT-02 | 범위 제외 | 실제 이동·회전하는 발판과 동적 IK. |
| REV-SPEED-01 | 하위 사례 확인 | `ceiling_surface_overlap_px`. 천장 충돌 표본. |
| REV-VIEW-01 | 보류 | DEC-06의 최종 좌표 계약. |
| REV-SAVE-01 | 보류 | 정확 저장·복원 정책. |
| REV-PERF-01 | 하위 사례 확인 | `moving_light_viewer_frame_ms`. SDL dummy 프레임 시간. 실제 장치 판정은 미실행. |
| REV-GOAL-01 | 하위 사례 확인 | `goal_requires_stop`. 속도·목표 지지. |
| SCOPE-01 | 하위 사례 확인 | `SCOPE-01`. 플레이 키 집합과 C/V 무효를 확인했다. 관계 데이터의 생산 스키마 검사는 별도다. |
| INPUT-01 | 하위 사례 확인 | `progress_key_edge_and_focus`. 진행 키 중복과 포커스. |
| INPUT-02 | 하위 사례 확인 | `pause_commit_boundary_and_closed_input`. 같은 시각 입력과 정지. |
| INPUT-03 | 하위 사례 확인 | `preparation_boundary_cancel`. Space 재입력과 준비 취소. |
| INPUT-04 | 하위 사례 확인 | `air_action_separate_from_motion`. 공중에서 추진 미발생. |
| INPUT-05 | 하위 사례 확인 | `opposed_keys_keep_walk`. 양쪽 방향 동시에 유지. |
| INPUT-06 | 하위 사례 확인 | `opposite_landing_compression_ticks`. 반대 방향 입력과 착지 압축. |
| INPUT-07 | 하위 사례 확인 | `INPUT-07`. 적격 E/F/G는 접지 회복 완료에서 수락하고 준비·공중에서 효과·예약·추진이 없었다. |
| INPUT-08 | 하위 사례 확인 | `INPUT-08`. C/V 미할당과 작업·공격·제동·진행 키의 바인딩을 검사했다. 기능별 비활성 토글은 활성 프로필에 없다. |
| INPUT-09 | 하위 사례 확인 | `progress_key_edge_and_focus`. 포커스 상실과 진행 키. |
| INPUT-10 | 하위 사례 확인 | `work_hint_matches_admission`. 공격 중 새 작업 입력 거절. |
| TIME-01 | 하위 사례 확인 | `timestamped_inputs_5_120fps`. 표시율별 동일 물리 결과. |
| TIME-02 | 하위 사례 확인 | `catch_up_debt_preserved`. 3초 경과 후 미처리 틱 보존. |
| TIME-03 | 하위 사례 확인 | `shared_work_clock`. 승인 후 작업 및 타격 시각. |
| TIME-04 | 하위 사례 확인 | `pause_commit_boundary_and_closed_input`. 일시정지 같은 틱의 입력과 이미 확정된 효과. |
| TIME-05 | 하위 사례 확인 | `TIME-05`. 3초 정지 후 지연 입력을 현재 틱에서 받아 1회 발사했다. 과거 요청의 저장·복원은 보류다. |
| JUMP-01 | 하위 사례 확인 | `preparation_boundary_cancel`. 준비 경계에서 같은 시각 입력으로 발사를 취소한다. |
| JUMP-02 | 하위 사례 확인 | `pending_jump_can_be_cancelled`. 회전 중 예약 취소. |
| JUMP-03 | 하위 사례 확인 | `JUMP-03`. 지지면 교체 또는 발사 예정 틱의 피격에서 발사와 가짜 회복이 없었다. 같은 지지에서의 별도 권한 토큰·end.blocked는 현행 프로필에 없다. |
| JUMP-04 | 하위 사례 확인 | `air_action_separate_from_motion`. 공중 동작 변경과 추가 발사 금지를 확인했다. |
| FALL-01 | 하위 사례 확인 | `air_action_separate_from_motion`. 공중에서 동작 변경 후 물리 유지. |
| LAND-01 | 하위 사례 확인 | `ceiling_surface_overlap_px`. 천장 접촉은 지지가 아니다. |
| LAND-02 | 하위 사례 확인 | `moving_landing_visible`. 이동 중 착지 표시. |
| LAND-03 | 하위 사례 확인 | `course_spawn_and_checkpoint_clearance`. 정적 시작 및 체크포인트. |
| INTERACT-01 | 하위 사례 확인 | `INTERACT-01`. 두 E 대상이 동시에 닿을 때 등불이 우선이며 표시와 수락이 일치했다. 활성화 후 씨앗을 선택한다. |
| INTERACT-02 | 하위 사례 확인 | `work_contact_admission_commit`. 시작과 효과의 접촉 확인. |
| INTERACT-03 | 현행 범위 밖 | 고정 대상은 동기 방식으로 판정한다. 객체 ID 재사용, 세대 및 비동기 응답 경합이 발생하는 프로필은 별도다. |
| INTERACT-04 | 하위 사례 확인 | `shared_work_clock`. 작업 효과 발생 시각. |
| INTERACT-05 | 하위 사례 확인 | `feed_to_move_restart_and_groom`. F와 G 전환 및 F 재입력. |
| INTERACT-06 | 범위 제외 | NPC 간 자원 경합. |
| INTERACT-07 | 하위 사례 확인 | `INTERACT-07`. E 유지 중 다음 대상의 자동 실행이 없고, 키를 떼어도 승인된 단발 작업이 완료됐다. 처리한 두 대상은 재수락되지 않았다. |
| INTERACT-08 | 하위 사례 확인 | `feed_count_5_120fps`. 섭식 횟수·잔량·표시율. |
| INTERACT-09 | 하위 사례 확인 | `phase_brake_and_groom_return`. 손질 취소와 표시 복귀. |
| INTERACT-10 | 하위 사례 확인 | `pause_resumes_effect_free_pose_return`. 중단 후 효과 없는 표시 복귀. |
| INTERACT-11 | 보류 | 정확 저장·복원. |
| COMBAT-01 | 하위 사례 확인 | `attack_active_end_excluded`. 공격 active 끝점 제외. |
| COMBAT-02 | 하위 사례 확인 | `connected_feed_and_readable_attack`. 새 X 처리와 섭식 효과 취소. |
| COMBAT-03 | 하위 사례 확인 | `COMBAT-03` 및 `JUMP-03`. 같은 틱 가시 접촉이 X·발사보다 우선했고 재피격 제한을 지켰다. 복수 공격자·넉백 합성은 현행 범위 밖이다. |
| COMBAT-04 | 하위 사례 확인 | `attack_hit_miss_cancel`. 정적 가시 대상의 명중·빗나감·취소 사례. |
| COMBAT-05 | 하위 사례 확인 | `moving_root_active_sweep_miss`. 공격 위치 교차 및 빗나감. |
| COMBAT-06 | 하위 사례 확인 | `COMBAT-06`. 공격 중 경계 실패에서 미실행 타격이 취소됐고 Space가 실패를 해제하지 않았다. 미완성 공격 프로필을 전환하는 기능은 없다. |
| RUN-01 | 하위 사례 확인 | `goal_requires_stop`. 목표 안정 체류. |
| RUN-02 | 하위 사례 확인 | `RUN-02` 및 `COMBAT-03`. 회수 발판의 정상 착지는 Playing을 유지하고 외부 낙하는 Failed로 끝났다. 고정 위험의 재피격 제한을 검사했다. |
| RUN-03 | 하위 사례 확인 | `RUN-03`. 등불이 켜진 3층 착지에서만 체크포인트를 활성화했다. 재착지에서 상태를 유지하며 수동 E 활성은 지원 범위 밖이다. |
| RUN-04 | 하위 사례 확인 | `course_spawn_and_checkpoint_clearance`. 재시작 위치 검증 및 App 완주 후 재시작. |
| DATA-01 | 하위 사례 확인 | `nearest_wall_and_configuration_validation`. 유한 시간·좌표·빈 트랙 검증. |
| DATA-02 | 하위 사례 확인 | `air_action_separate_from_motion`. 공중 Idle의 물리와 표시. |
| DATA-03 | 하위 사례 확인 | `reference_shader_equivalence`. 채널 처리·기준 이미지 비교. |
| DATA-04 | 하위 사례 확인 | `support_labels`. 보조 셀 지지·마커. |
| DATA-05 | 하위 사례 확인 | `course_validation_and_cache_isolation`. 에셋 인스턴스 캐시 분리와 로더 검사. |
| DATA-06 | 보류 | 정확 저장·복원과 경계 추적. |
| DATA-07 | 하위 사례 확인 | `replanted_spin_10_60fps`. Z 지지·스윙과 저장 Action의 120셀 지오메트리 대조. |

[실행 회귀 결과](verification.json) · [변경 기록](PATCH_NOTES.md)
