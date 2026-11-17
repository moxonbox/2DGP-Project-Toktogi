# 비거미류 8종 2DGP Movement 명세서 색인

> 2026-11-17 · ZIP 원본 8종에서 파생된 2DGP AI 동작·애니메이션 명세. 종별 본문은 약 100줄을 목표로 하며 원본 연구 문서와 함께 읽는다.

| 객체 | 역할·핵심 동작 | 종별 톡토기 근거 | 파일 |
|---|---|---|---|
| `predator_hydrometra_stagnorum` | 수면 진동 감지·느린 추적·관통흡즙 | `photo_report_species_identification_unverified` | [predator_hydrometra_stagnorum_movement.md](../C221_hydrometra_stagnorum/document/predator_hydrometra_stagnorum_movement.md) |
| `predator_hydrometra_martini` | 기질-먹이 조합에 따른 느린 접근·흡즙 | `different_sminthurides_species_rearing` | [predator_hydrometra_martini_movement.md](../C222_hydrometra_martini/document/predator_hydrometra_martini_movement.md) |
| `predator_microvelia_reticulata` | 수면 빠른 보행·활주·주둥이 접촉 | `collembola_unspecified_species_observed` | [predator_microvelia_reticulata_movement.md](../C231_microvelia_reticulata/document/predator_microvelia_reticulata_movement.md) |
| `predator_mesovelia_vittigera` | 부유잎 보행·수면 횡단·흡즙·청소 | `habitat_overlap_not_confirmed_predation` | [predator_mesovelia_vittigera_movement.md](../C241_mesovelia_vittigera/document/predator_mesovelia_vittigera_movement.md) |
| `predator_stenus` | 지면 배회·아랫입술 사출/위턱 공격 분기 | `springtail_capture_multiple_stenus_species` | [predator_stenus_movement.md](../C251_stenus/document/predator_stenus_movement.md) |
| `predator_gambusia_holbrooki` | 물속 유영·수면 접근·입 벌려 먹이 채기 | `Sminthurides_genus_found_in_diet_study` | [predator_gambusia_holbrooki_movement.md](../C261_gambusia_holbrooki/document/predator_gambusia_holbrooki_movement.md) |
| `predator_pergamasus_crassipes` | 토양 틈 이동·협각 포획·먹이 씹기 | `terrestrial_collembola_prey_not_aquaticus` | [predator_pergamasus_crassipes_movement.md](../C271_pergamasus_crassipes/document/predator_pergamasus_crassipes_movement.md) |
| `predator_rana_temporaria` | 뒷다리 도약·착지·물갈퀴 수영·혀 포획 | `Podura_aquatica_experiment_not_aquaticus` | [predator_rana_temporaria_movement.md](../C281_rana_temporaria/document/predator_rana_temporaria_movement.md) |

**공통:** NPC는 관계·짝짓기·결속 기능이 아닌 탐색→접촉→공격/섭식→종료의 일시 이벤트를 사용한다. AI/물리/리그/2D 표시 소유권을 분리한다. 모든 게임 수치·공격 성공률은 실측값이 아니며 명세의 `null` 항목은 정해야 한다.

**중요:** 종별 `toktogi` 직접 포식 미확인을 게임적 적 AI 배치 근거와 혼동하지 않는다. 자생 분포가 없는 종은 한국 자연 수역의 실제 천적으로 소개하지 않는다.

**출력:** 8개 개별 Markdown, 총괄 색인 1개; 원본 ZIP 생물 문서(저작자 출처·참고 연구 링크)는 변형 없이 별도로 유지한다.
