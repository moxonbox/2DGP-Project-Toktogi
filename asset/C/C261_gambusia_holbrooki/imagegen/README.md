# GPT Image 원화와 사용 범위

내장 GPT Image로 생성·수정했다. 모델 세부 버전과 seed는 도구가 제공하지 않았다.

- `user_appearance_target.png`: 사용자가 지정한 최종 외관 기준.
- `female_sprite_style_key.png`: 앞서 생성한 직접 Sprite 개선 원화. 기준 자료이며 실행 프레임은 아니다.
- `female_uv_atlas_raw.png`, `male_uv_atlas_raw.png`: 이번 수정에 사용한 암수 unlit UV pigment 원시 결과. 수컷은 gravid spot을 제거했다.
- `female_uv_prompt_r03.txt`, `male_uv_prompt_r03.txt`: 현재 원시 결과의 실제 편집 프롬프트.
- `manifest.json`: 역할·크기·SHA256.

다른 `*_prompt.txt`는 앞선 생성 이력이다. 이전 실행 에셋 전체는 `../3D/versions/gambusia-r01.7z`에 보존했다.

원시 1254² atlas는 Blender 표준 이미지 축소로 1024² 작업 텍스처에 수용했다. 원시 PNG는 변경하지 않았다. 실제 Sprite는 수정된 눈·아가미 메시, 기존 96 Actions와 카메라로 재출력했다. 몸 13색, 4단 명암, 2px 외곽선, 640²/384² 셀을 유지한다. 2,304장을 GPT Image가 개별 생성한 것은 아니다.
