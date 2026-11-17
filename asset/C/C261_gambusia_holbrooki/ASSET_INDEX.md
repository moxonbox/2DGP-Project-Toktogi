# C261 · Gambusia holbrooki · gambusia-r03

첨부 외관을 기준으로 올리브색 등, 밝은 아이보리 배·볼, 큰 검은 눈과 반사점, 아가미 덮개, 지느러미 선을 수정했다. GPT Image UV 원화를 편집 가능한 3D 모델에 적용하고 모든 모션을 재출력했다.

- [암컷 idle](2D/gambusia-r03/female_hover_or_school_mid_left.png) · [수컷 idle](2D/gambusia-r03/male_hover_or_school_mid_left.png)
- [전후 비교 · 1×](comparison/sprite_imagegen_before_after.png) · [모션 검사](GambusiaMotionPreview.html) · [연못 실행](PlayGambusia.cmd)
- [GPT Image 원시 결과·프롬프트](imagegen/README.md) · [구현·검수 기록](document/IMPLEMENTATION.md)
- [원본 r01 전체 보관](3D/versions/gambusia-r01.7z) · [복원 지도](3D/versions/restore_map.json)
- [현재 Blender](3D/gambusia_holbrooki_r03.blend) · [배포 해시](delivery_manifest.json)

원본 5,362파일은 별도 폴더에 압축 해제하고 SHA256으로 복원 일치를 확인했다. 이전 3D·PNG·번들·HTML·문서를 모두 포함한다. 생물·모델·동작 명세 3개는 현재 폴더에도 그대로 유지한다.

암컷 640² / 수컷 384², C011 대비 SL 6배 / 3.5배, 71.910112px/BU, 몸 전용 13색, 4단 명암, #22313B·2px 외곽선을 유지한다. 암수 × 16행동 × 3구간 × 4시점, 총 2,304셀의 8패스를 재생성했다. 눈·아가미 수정에 따라 관련 Normal/AO/coverage 등도 새 모델에서 계산한다. 피벗·카메라·시간표·SL 마커는 유지한다.

기본 실행 외관은 Sprite다. `L`은 별도 연속 재조명 모드이며 원화와 명암이 다르다. `1` 표층, `2` 돌파, `3` 포획, `4` 회피, `M` 암수, `P` 일시정지. F2는 기존 톡토기 검사기다.

실제 브라우저·GPU는 미검증, Pico2D는 미연결이다. 측정 성능은 [acceptance_summary.json](document/acceptance_summary.json)을 따른다. 첨부 이미지를 픽셀 단위로 복제한 결과는 아니며, 고정 크기와 3D 모션 정합에 맞춘 해석본이다.
