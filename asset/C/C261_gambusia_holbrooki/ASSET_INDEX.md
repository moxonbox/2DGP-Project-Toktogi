# C261 · Gambusia holbrooki · gambusia-r01

성체 암수 모델을 GPT Image 시트에 맞춰 수정했다. 눈 돌출을 낮추고 위향 입·아가미 덮개/홈·둥근 꼬리지느러미·등지느러미 부착·가슴/배지느러미·고정 지느러미 무늬를 정리했다. 암컷의 깊은 배와 gravid spot, 수컷의 가는 몸과 gonopodium을 구분한다.

- [최종 Blender](3D/gambusia_holbrooki_r01.blend) · [수정 전후](comparison/model_detail_before_after.png)
- [암컷 기준 시트](sheet/gambusia_female_sheet_r01.png) / [최종 6면](sheet/blender_female_sheet.png)
- [수컷 기준 시트](sheet/gambusia_male_sheet_r01.png) / [최종 6면](sheet/blender_male_sheet.png)
- [모션 검사 HTML](GambusiaMotionPreview.html): 암수 × 16행동 × pre/mid/end × 4시점 × 8패스. 재생·프레임 이동·fps·정수 확대·소켓·실제 물리 기록 시퀀스.
- [연못 실행](PlayGambusia.cmd): 기존 톡토기 App/플레이어/충돌을 재사용하는 선택 실행본. 기존 게임 기본 진입점은 바꾸지 않았다.
- [인수·제약 기록](document/IMPLEMENTATION.md) · [원본/크기/스타일 계약](document/source_contract.json) · [변경 파일 해시](delivery_manifest.json)

암컷 SL 60mm·수컷 35mm의 상한에 사용자 선택 연출계수 0.1을 적용했다. C011 체장 대용값 대비 **6배 / 3.5배**, SL **5.792376 / 3.378886BU**. 생물 실측 m 단위 모델이 아니다. 동일 71.910112px/BU로 암컷 640², 수컷 384² 셀을 출력했다. 모델 TL은 SL과 별도다.

Blender 5.3.0 저장본: 암컷 4,160삼각형·수컷 4,164삼각형, 각각 26본, 총 96 Action. 루트는 물리와 시각을 분리한다. 왼쪽/오른쪽은 별도 렌더이며 PNG 미러링하지 않는다. front/top은 검사 시점이다.

실행에는 Python, `requirements.txt` 패키지와 프로젝트의 기존 C011 실행 번들이 필요하다.

```powershell
python -m pip install -r requirements.txt
python runtime/gameplay.py
python runtime/verify_runtime.py
node runtime/verify_preview.js
```

연못 조작: `1` 표층 노출, `2` 돌파, `3` 표층 포획, `4` 회피, `M` 암수, `L` Sprite/재조명, `P` 일시정지. F2는 기존 톡토기 검사기로 전환하며 물고기 물리를 멈춘다. 물고기의 모든 클립 검사는 HTML에서 한다. 돌파는 기본 FishSim에서는 꺼져 있고, 이 선택 실행본에서만 명시적으로 켠다.

이식할 때 `2D/`, `3D/`, `runtime/`, `sheet/`, `previews/`, `comparison/`, `document/`와 루트 HTML을 함께 유지한다. 런타임은 ZIP과 `.source.json` 잠금을 함께 읽는다. HTML은 같은 폴더의 아틀라스/기록 PNG를 읽는다. 검사 시트/APNG를 실제 개별 적층 PNG와 혼동하지 않는다.
