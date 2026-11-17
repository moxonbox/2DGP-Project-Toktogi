# 톡토기 천적 3D 모델링 명세서 색인

> **기준 파일:** `toktogi_model.md` · **종 대상:** *Sminthurides aquaticus* · **작성일:** 2026-11-17
> **범위:** 기존 천적 객체 11개 / 그룹 6개. 파일은 생물학적 외형 가이드이며 실제 3D 메시를 포함하지 않습니다.

## 그룹별 객체

| 그룹 | 3D 모델 명세서 | 분류 수준 |
|---|---|---|
| 거미류 | [Pardosa spp.](../C211_spider_paradosa/document/spider_pardosa_model.md) | 속 · 116줄 |
| 거미류 | [Linyphiidae](../C212_spider_linyphiidae/document/spider_linyphiidae_model.md) | 과 · 116줄 |
| 거미류 | [Triaeris stenaspis](../C213_spider_stenaspis/document/spider_triaeris_stenaspis_model.md) | 종 · 115줄 |
| 수면 노린재류 | [Hydrometra stagnorum](../C221_hydrometra_stagnorum/document/predator_hydrometra_stagnorum_model.md) | 종 · 114줄 |
| 수면 노린재류 | [Hydrometra martini](../C222_hydrometra_martini/document/predator_hydrometra_martini_model.md) | 종 · 114줄 |
| 수면 노린재류 | [Microvelia reticulata](../C231_microvelia_reticulata/document/predator_microvelia_reticulata_model.md) | 종 · 114줄 |
| 수면 노린재류 | [Mesovelia vittigera](../C241_mesovelia_vittigera/document/predator_mesovelia_vittigera_model.md) | 종 · 114줄 |
| 딱정벌레류 | [Stenus spp.](../C251_stenus/document/predator_stenus_model.md) | 속 · 114줄 |
| 포식성 응애류 | [Pergamasus crassipes](../C271_pergamasus_crassipes/document/predator_pergamasus_crassipes_model.md) | 종 · 114줄 |
| 어류 | [Gambusia holbrooki](../C261_gambusia_holbrooki/document/predator_gambusia_holbrooki_model.md) | 종 · 116줄 |
| 양서류 | [Rana temporaria](../C281_rana_temporaria/document/predator_rana_temporaria_model.md) | 종 · 115줄 |

## 통일된 모델링 규칙

- 모델 단위: mm(1.0 게임 단위로 변환할 때 물리 단위와 스케일 인자를 명시).
- 몸길이와 다리 편 길이, 어류 표준체장(SL)/전장(TL), 개구리 몸길이를 혼동하지 않는다.
- 종 미선정인 `Pardosa`/`Linyphiidae`/`Stenus`는 **속·과 형태 가이드**이므로 종별 색·비율은 선택 후 고정한다.
- 이 목록에서 **물알둥근톡토기를 직접 포식한 것으로 확정 동정된 천적 종은 없음**. *Hydrometra stagnorum*은 사진 보고에 근거한 재동정 대기.
- 성별, 유체/성체, 날개 다형, 양서류 변태, 어류 생식 지느러미 등의 변형은 개별 모델 또는 슬롯으로 분리한다.
- LOD0는 구별 특징, LOD1은 주요 실루엣, LOD2는 큰 형상과 색만 유지한다. 본/마테리얼의 정확한 수량은 프로젝트 제작 정책에 따라 결정한다.
- 재질 수치, 노멀 맵 깊이, 토폴로지 수, 애니메이션 초당 속도 등은 **생물 실측자료가 아닌 제작 설정**이다.

## 출처 해석과 검증

- 각 파일의 **원명세서**가 행동·생태 관계 근거이고, `[P1]` 등의 외부 링크는 해부학·크기·동정용 참고다.
- 같은 속의 다른 종에서 제시된 무늬와 크기는 모델에 복사하기 전에 반드시 종을 식별해야 한다.
- 모델 완료 전 **등·정·측·복면**, 관절 접합부, 실측 크기 기준, 성별/날개형 차이를 점검한다.
- 원본 사진·도표를 직접 메쉬나 텍스처로 전재할 때는 원저작자 이용권한을 별도 확인한다.
