# 3D 모델의 2D 스프라이트 변환 및 재질·조명 재현 기술 검토

> 파일명: `3Dconv2D.md`  
> 작성일: 2026-11-02  
> 범위: Python·Pico2D 기반 2D 렌더링. 외부 런타임 라이브러리 미적용/적용 방식을 비교한다.  
> 문서 성격: 기술 선택을 위한 설계 검토. 예시 구성은 구현·성능 검증 완료를 의미하지 않는다.

## 1. 목적과 핵심 결론

Blender 등에서 만든 3D 모델의 외형을 **2D 스프라이트**로 변환하면서, 원본 재질의 **Base Color, Normal, Ambient Occlusion(AO), Height, Metallic, Roughness, Emissive, Depth** 등의 정보도 2D에서 재사용하고, 게임 실행 중 광원에 반응하게 하는 방법을 정리한다.

다음 세 문제를 **독립적으로** 선택해야 한다.

1. **외형 생성:** 일반 렌더, 저해상도 직접 렌더, 고해상도 렌더 후 픽셀화, 복셀/블록 모델 렌더 등.
2. **데이터 보존:** 완성 RGBA 이미지만 저장할지, 각 표면의 재질값을 화면 좌표계의 보조맵으로 함께 저장할지.
3. **실행 중 조명 계산:** 사전 제작한 이미지 선택·합성, CPU 픽셀 계산, GPU 셰이더 중 무엇을 사용할지.

**요지:** 단일 완성 PNG에는 렌더 당시의 재질 *결과*가 남을 뿐, 원본 3D 재질이 자동으로 살아남는 것은 아니다. 동적 재조명을 원한다면 스프라이트와 좌표가 맞는 재질·표면 데이터와 이를 처리할 계산 경로가 필요하다.

## 2. 비교 조건과 용어

| 조건 | 게임 실행 환경 | 가능한 접근 | 주요 한계 |
|---|---|---|---|
| **A. 외부 라이브러리 미적용 — Pico2D 기본 API만** | Python 표준 라이브러리 + Pico2D 기본 이미지 기능 | 완성 렌더 이미지, 조명별 이미지 선택, 알파/레이어 표현 | 사용자 정의 픽셀 셰이더와 고수준 픽셀 버퍼 갱신 기능 부재 |
| **A-확장. 새 패키지 설치 없이 SDL 계층 직접 이용** | Python·Pico2D 설치 환경에 포함된 SDL 의존성 접근 | 합성 모드 확대, CPU 조명 계산 결과를 동적 텍스처에 업로드 | Pico2D 고수준 API를 벗어나는 연동 코드·자원 관리 필요 |
| **B-1. 외부 라이브러리 추가 + Pico2D 유지** | 예: NumPy, Pillow + Pico2D/SDL | 픽셀별 CPU 조명, 자동 이미지 후처리, 텍스처 갱신 | 업로드 경로와 CPU 연산량이 병목 가능 |
| **B-2. GPU 계산 + Pico2D 최종 출력** | 예: ModernGL 오프스크린 + Pico2D | 셰이더로 계산 후 픽셀을 읽어 SDL 텍스처로 전달 | GPU→CPU 읽기 및 재업로드 비용, 컨텍스트 연동 |
| **B-3. GPU 기반 출력으로 교체** | 예: ModernGL + moderngl-window 또는 Arcade + arcade.gl | 2D 스프라이트에 사용자 정의 조명/PBR/깊이 셰이더 | Pico2D가 최종 출력 주체가 아니게 됨; 렌더러 이식 필요 |

**외부 라이브러리 적용 여부는 게임 실행 시점을 기준**으로 구분한다. Blender 및 `bpy`는 오프라인 제작 도구이므로 이 비교에서 런타임 라이브러리로 세지 않는다. 별도 제작용 이미지 도구만 추가하는 절충안도 가능하다.

## 3. 3D에서 2D 스프라이트를 만드는 방식

| 방식 | 제작 순서 | 적합한 결과 | 주의점 |
|---|---|---|---|
| **완성 렌더 → RGBA** | 3D 모델·재질·광원 렌더 → 투명 PNG | 사실적인 사전 조명 2D 캐릭터·소품 | 새로운 광원에 따라 표면 반응을 정확히 변경하기 어려움 |
| **저해상도 직접 렌더** | 3D 장면을 작은 픽셀 격자로 렌더 → 필요 시 정수배 확대 | 픽셀풍 실루엣·일관된 격자 | 머리카락·더듬이·세부 모양 소실 가능 |
| **고해상도 렌더 후 픽셀화** | 충분히 크게 렌더 → 축소·팔레트/디더링·윤곽 정리 | 미술적으로 조절 가능한 픽셀풍 | 색상 이미지용 후처리를 노멀/깊이 데이터에 그대로 적용하면 안 됨 |
| **복셀·블록 스타일 모델 렌더** | 실제 3D 메시를 복셀/블록 형태로 수정 → 렌더 | 각진 면과 블록형 입체감 | 원래 형상이 바뀌므로 노멀·그림자도 새 형상 기준 |
| **방향별·포즈별 멀티패스 렌더** | 여러 카메라 방향·애니메이션 프레임에서 RGBA+재질 패스 출력 | 360° 회전, 재조명 스프라이트 | 방향×포즈×맵 수에 비례하는 데이터 증가 |
| **깊이 포함 임포스터** | 색상+깊이·노멀·위치 등의 보조맵 저장 | 제한적 시점 보정, 픽셀별 위치 조명·가림 | 단일 시점에서 가려진 뒷면은 복원 불가 |

`3D를 픽셀화`하는 방식과 `3D 렌더를 2D 이미지로 사용`하는 방식 모두 **보조 재질 맵 저장 및 동적 조명**과 조합할 수 있다. 픽셀화는 미술 표현, 재질 맵은 데이터 표현, 조명식은 실행 기능이다.

## 4. Blender에서 재질을 화면 좌표의 2D 맵으로 출력

### 4.1. UV 텍스처와 스프라이트 맵의 차이

원본 모델의 UV 텍스처는 **펼친 3D 표면상의 UV 좌표**에 대응한다. 완성 스프라이트는 **카메라에 투영된 픽셀 좌표**에 대응하므로 UV용 Normal·Metallic·Roughness 이미지를 그대로 스프라이트 위에 붙이는 것은 일반적으로 맞지 않는다.

권장 흐름:

```text
3D 모델 + 재질 노드 + 애니메이션
            ↓
방향·포즈·카메라 고정
            ↓
렌더 패스 / Shader AOV로 표면 속성 추출
            ↓
동일한 화면 좌표에 정렬된 RGBA + 재질 맵
            ↓
크롭·피벗·아틀라스·메타데이터 정리
            ↓
게임에서 이미지 선택 및 조명 계산
```

Blender의 UV 베이크와 카메라에서 보이는 화면 좌표의 Render Pass/AOV 출력은 목적이 다르다. 스프라이트용 맵 생성에 UV 베이크가 항상 필수인 것은 아니다. 노드 구조와 렌더 엔진·버전에 따라 어떤 값이 AOV로 나오는지 확인해야 한다.

### 4.2. 보존 대상별 기능과 한계

| 맵 | 담아야 할 정보 | 2D 런타임 사용 | 혼동하기 쉬운 점 |
|---|---|---|---|
| **Base Color / Albedo** | 조명 적용 전 표면 기본색 | 확산·반사 계산의 색 성분 | *완성 렌더의 명암*이 섞이면 재조명에서 이중 적용 가능 |
| **Alpha / Coverage** | 스프라이트의 실루엣·투명도 | 마스킹·합성·아틀라스 처리 | 다른 맵과 크롭·경계가 일치해야 함 |
| **Normal** | 보이는 표면의 방향(범프 포함 여부 명시) | 광원 방향에 따른 확산·반사 | 좌표계·축·색공간·정규화 필요; 그림자와 실루엣을 자동 생성하지 않음 |
| **AO** | 국소 주변광 차폐 정도 | 환경광/간접광 약화 | 이동 광원에 의한 직접 그림자와 다름 |
| **Height** | 표면의 상대 높이·요철 | Bump, Parallax, 제한적 자기 가림 | 카메라 Depth나 월드의 높이 z와 다름 |
| **Depth** | 카메라에서 보이는 표면까지의 깊이 | 픽셀별 위치 복원·정렬·시점 보정 | 보이지 않는 뒷면 정보 없음 |
| **Position** | 보이는 표면의 객체/월드/카메라 위치 | 점광원 거리·정반사 시선 방향 | 공간 좌표계·단위·카메라 정보 필요 |
| **Metallic** | 금속성(보통 0~1) | 금속/비금속의 BRDF 분리 | 단순 ‘반짝임 강도’가 아님 |
| **Roughness** | 표면 미세 거칠기 | 하이라이트·반사 분포 | 단순 명암 대비와 같지 않음 |
| **Emissive** | 방출 색과 밝기 | 표면 자체의 발광 | Bloom 및 주변을 밝히는 광원은 별도로 구현 |
| **기타(선택)** | Coat, Transmission, IOR, Anisotropy, Thickness 등 | 코팅·투명·투과 등 | 표준 단일 표면 맵만으로 복잡한 다층 재질을 완전 재현하기 어려움 |

**중요:** Blender의 `Diffuse Color` 패스를 무조건 Principled BSDF의 모든 재질에 대한 `Base Color`로 취급하지 않는다. 금속 재질 등의 경우 원래 *Base Color 입력값*을 Shader AOV로 별도 출력하는 구성이 더 명확하다. 복합 BSDF·시점 의존 재질은 각 입력값만으로 원래 결과를 완전히 복원하지 못할 수 있다.

### 4.3. Normal의 좌표계와 인코딩

- **카메라 공간 Normal:** 현재 화면 시점을 기준으로 쓰기 편하나 방향별 영상과 변환을 일치시켜야 한다.
- **객체 공간 Normal:** 게임 속 객체 회전에 따라 변환할 수 있다.
- **월드 공간 Normal:** 월드 광원과 직접 결합할 수 있으나, 원본 렌더 당시 객체 회전 정보가 반영된 데이터인지 주의한다.
- 원래 모델의 **tangent-space Normal**은 UV 접선 기준이므로 스프라이트에 사용하려면 보이는 표면의 실제 방향으로 변환해야 한다.

벡터 `N`의 성분이 `[-1,1]`일 때 RGB8에 인코딩하는 한 예:

```text
RGB = 0.5 * (N + 1)
N   = normalize(2 * RGB - 1)
```

파일과 렌더러에서 **R/G/B 축 방향, Y축 상하, 선형 데이터 처리, 뒤집기·회전 시 벡터 변환**을 통일한다. Blender의 Normal 패스가 범프·노멀맵까지 어떤 식으로 반영되는지는 출력 경로와 테스트 장면에서 검증한다.

### 4.4. 제작 시 함께 기록할 메타데이터

- 스프라이트 방향 기준·순서, 카메라 각도와 투영 형식.
- 애니메이션명·프레임 시간·재생 규칙.
- 원본 캔버스 크기, 크롭 사각형, 프레임 배치 피벗.
- 각 맵의 크기·좌표계·채널 정의·색공간.
- Normal 인코딩 방식, Depth/Height의 단위·기준·범위.
- 아틀라스 페이지·사각형·패딩 및 미사용 채널의 기본값.

모든 재질 맵은 **같은 포즈·카메라·실루엣·크롭·피벗·아틀라스 위치**를 따라야 한다.

## 5. 2D에서 조명에 반응시키는 방법

### 5.1. 방법별 개요

| 방식 | 사용 데이터 | 조명 변화 자유도 | 구현 비용 | 특징 |
|---|---|---|---|---|
| **완성 이미지 선택** | RGBA | 저장한 조건만 | 낮음 | 재질 결과가 가장 직접적으로 보존되지만 동적 반응 제한 |
| **조명 방향·상태별 이미지 전환** | 여러 완성 RGBA | 이산적 | 낮음~중간 | 빛의 방향/환경 조건이 늘면 용량 증가 |
| **베이크된 조명 레이어 합성** | 알파·하이라이트·그림자 등 | 제한적 | 낮음~중간 | 정확한 다중 조명/물리식은 아님 |
| **Normal 기반 Lambert 조명** | Base Color, Normal, 선택 AO/Emission | 연속적 확산 조명 | 중간 | 이동 광원의 빛 방향을 반영 |
| **2D 스프라이트 PBR** | Base Color, Normal, Metallic, Roughness, 위치·시선 등 | 재질별 직접광 반응 | 중간~높음 | BRDF 계산과 색공간·환경광 규약 필요 |
| **Height/Parallax/Relief** | Height 및 여러 재질 맵 | 작은 시점 이동의 시차·요철 | 높음 | 정확한 형상/뒷면을 자동 생성하지 않음 |
| **Depth/Position 임포스터** | Depth/Position/Normal/색상 | 위치 기반 조명, 제한적 가림·재투영 | 높음 | 보이지 않는 면과 큰 회전 시 빈 영역의 한계 |
| **기저 조명/RNM/PTM 계열** | 조명 응답 이미지/계수 | 사전 학습·설계한 범위에서 근사 | 중간~높음 | 재질 파라미터 대신 조명 반응을 저장할 수 있음 |

### 5.2. Normal 확산 조명

선형 색공간에서의 단순한 예시:

\[
C = A\left(k_a AO + \sum_i c_i a_i \max(N\cdot L_i,0)\right) + E
\]

- `A`: 조명 전 Base Color, `N`: 단위 표면 Normal, `L_i`: 표면에서 i번 광원으로 향하는 단위 벡터.
- `c_i`: 광원 색·강도, `a_i`: 광원과 표면 사이 거리 감쇠, `k_a`: 주변광, `E`: Emissive.
- 위 식은 **교육용 단순 확산 모델**이며, 반사·간접광·정교한 그림자를 모두 포함하지 않는다.
- 점광원은 픽셀별 광원 방향과 거리를 구해야 하므로 표면 위치를 알아야 한다. Position 맵 또는 카메라·Depth에서 복원한 위치를 이용할 수 있다.

### 5.3. Metallic/Roughness PBR

- Base Color, Normal, Metallic, Roughness, 표면 위치, 광원 위치/방향, 시선 방향을 이용해 BRDF를 평가한다.
- 금속에서는 Base Color가 주로 반사색에 영향을 주고, 비금속에서는 확산색 역할을 한다.
- Roughness는 반사 분포의 폭과 선명도에 관여한다.
- 환경맵 기반 IBL은 선택적 확장이다. 없더라도 직접광 PBR 계산은 가능하지만 주변 환경 반사 표현은 제한된다.
- 2D 한 픽셀에 보이는 표면 하나만 저장하면 3D 전체 장면의 복잡한 투과·다층 반사까지 그대로 재현하지는 못한다.

### 5.4. AO / Emissive / 그림자는 각각 구분

- **AO:** 주변광의 국소 차폐. 직접광 그림자를 대신하지 않는다.
- **Emissive 표면:** 해당 픽셀 자체를 밝게 보이게 한다.
- **Bloom:** 밝은 픽셀 주변의 후처리 빛 번짐.
- **주변 물체에 빛을 비춤:** 별도의 광원 또는 간접광 계산이 필요하다.
- **실제 물체 간 그림자/가림:** 깊이·기하 구조 또는 그림자용 별도 계산이 필요하다.

### 5.5. Height, Depth, 시점 재투영

- Height에서 기울기를 구해 Bump/Normal을 근사할 수 있다.
- Parallax는 시선 방향과 Height에 따라 텍스처 좌표를 옮긴다. 정교한 Relief/Parallax Occlusion은 반복 샘플링과 자체 가림 처리가 필요하다.
- Depth는 보이는 표면까지의 카메라 방향 거리이며, Height와 역할이 다르다.
- Depth를 포함한 임포스터는 픽셀별 위치 조명·가림·작은 시점 차이 보정에 쓰일 수 있지만 **단일 시점에서 가려진 면은 복원할 수 없다**.
- 여러 시점·여러 깊이층을 저장하면 그 한계를 줄일 수 있지만 저장량·셰이더 복잡도가 증가한다.

### 5.6. 사전 계산한 조명 응답의 보간

여러 조명 조건에 대한 응답 이미지/계수 `B_i`를 저장하고 현재 광원의 가중치 `w_i`로 조합하는 근사 방식도 있다.

\[
C(p) \approx \sum_i w_i B_i(p)
\]

RNM, PTM 등의 계열은 이런 취지를 갖지만 실제 계수·조합식은 기법마다 다르다. 일반 알파 합성과 동치가 아니며, 시점이 크게 변하거나 날카로운 금속 반사가 이동하는 조건은 어려울 수 있다.

## 6. 외부 라이브러리 미적용: Python + Pico2D

### 6.1. Pico2D 기본 이미지 기능만 이용

사용 가능한 접근:

1. Blender에서 조명과 재질을 완전히 렌더한 PNG를 출력.
2. 조명 방향별/상태별 버전을 추가로 만들어 선택.
3. 투명 이미지·미리 계산한 하이라이트·그림자·발광 레이어를 겹쳐 연출.
4. 필요시 간단한 보간이나 색 효과를 구성.

한계: `load_image()` 등으로 **맵을 읽을 수 있다**는 것과, 그 픽셀을 읽고 사용자 정의 조명식을 적용할 **셰이더·픽셀 갱신 경로가 있다**는 것은 다른 문제다. Pico2D의 기본 고수준 이미지 API에는 이 기능들이 바로 제공되지 않는다.

일반 알파 오버 합성과 가산 합성은 다르다.

```text
일반 합성: C_out = alpha * C_source + (1-alpha) * C_dest
가산 합성: C_out = alpha * C_source + C_dest
```

따라서 일반 투명 이미지 여러 장을 그리는 것만으로 물리적인 다중광원 합이 자동으로 구현되지는 않는다.

### 6.2. 별도 패키지 설치 없이 기존 SDL 기능 활용

Pico2D 설치 환경에 포함된 SDL 계층을 접근할 수 있다면, 기본 API 바깥에서 다음을 구현하는 방안을 검토할 수 있다.

- SDL의 추가 텍스처 블렌딩 모드 사용.
- Python `array`, `bytearray`, `struct` 등으로 CPU 픽셀 버퍼 구성.
- 계산 결과를 SDL 동적 텍스처로 갱신하여 출력.

```text
[Base/Normal/AO/Emission 배열]
                ↓
       표준 Python 픽셀 연산
                ↓
         RGBA 픽셀 버퍼
                ↓
     SDL 동적 텍스처 갱신
                ↓
           화면 출력
```

확인할 사항: 실제 Pico2D/SDL 버전과 렌더러 핸들 접근, 픽셀 포맷, 행 간격(`pitch`), 버퍼 수명, lock/unlock, 텍스처 해제, 렌더링 상태 복원. **이는 새 패키지를 설치하지 않는 방식이지, Pico2D의 공식 고수준 API만 사용하는 방식은 아니다.**

원리상 픽셀별 PBR도 가능하지만, 표준 Python의 순수 픽셀 루프는 큰 이미지·다중광원에서 매우 느려질 수 있으므로 측정이 필요하다.

## 7. 외부 라이브러리 적용

### 7.1. 오프라인 제작 도구만 추가 — 런타임은 Pico2D 유지

- **Pillow:** 이미지 로딩·축소·트리밍·채널 확인·후처리.
- **NumPy:** 멀티패스 배열 처리와 자동 검증.
- **rectpack:** 잘라낸 프레임 사각형의 아틀라스 배치.
- **PNG 최적화 도구:** 배포 파일의 압축 최적화.

이 도구들은 제작 단계에만 사용 가능하다. 런타임에서 계속 Pico2D를 사용할 수 있으며, 다만 **오프라인 도구 추가만으로 동적 셰이더 기능이 생기는 것은 아니다.**

### 7.2. Pico2D 유지 + NumPy / Pillow CPU 재조명

```text
Blender RGBA + 재질 패스
             ↓
    Pillow 로딩 / NumPy 배열
             ↓
    노멀·광원·PBR 픽셀 계산
             ↓
     RGBA8 출력 버퍼 작성
             ↓
    SDL 텍스처 갱신 및 Pico2D 출력
```

- NumPy는 CPU에서 대량 배열 연산을 효율적으로 수행할 수 있게 하지만 **GPU 셰이더로 자동 전환되는 것은 아니다**.
- Pillow는 편의상 사용하며 반드시 필요한 것은 아니다.
- 결과물을 디스크 PNG로 매 프레임 기록하고 재로드하는 대신 메모리 버퍼를 직접 업데이트하는 경로가 적합하다.
- 작은 스프라이트·낮은 논리 해상도·광원 한 개로 시작하여 CPU 시간과 버퍼 업로드 시간을 별도 측정한다.

### 7.3. GPU 셰이더 계산 + Pico2D 최종 출력

GPU 라이브러리로 오프스크린 이미지에 재질 셰이더를 적용한 후:

1. GPU 결과를 CPU 메모리로 읽어 온다.
2. SDL 텍스처에 다시 업로드한다.
3. Pico2D의 기존 화면 출력과 결합한다.

**가능한 아키텍처이지만 전송·동기화 병목**이 있다. GPU 계산만의 속도로 판단하지 않고 읽기·업로드를 포함한 전체 프레임 비용을 측정해야 한다. 동일 창의 렌더 컨텍스트를 공유하는 직접 통합은 백엔드·자원 소유권·렌더 순서 연동이 필요한 별도 과제다.

### 7.4. GPU 렌더러가 최종 출력을 맡도록 변경

| 후보 | 성격 | 장점 | 과제 |
|---|---|---|---|
| **ModernGL + moderngl-window** | 셰이더·텍스처·프레임버퍼를 직접 구성 | 재질·깊이·PBR 실험 자유도 높음 | 입력·창·스프라이트 배치·리소스 관리 직접 설계 |
| **Arcade + arcade.gl** | 2D 게임 기능 및 GPU 확장 | 스프라이트 관리와 셰이더 적용을 함께 다루기 편함 | 비표준 PBR/Depth/투명 가림 등은 별도 구현 |
| **PyOpenGL + 창 관리 라이브러리** | 저수준 OpenGL 바인딩 | API를 직접 제어 | 가장 많은 그래픽 상태·기능을 직접 관리해야 할 수 있음 |

**주의:** 이것은 `Python + Pico2D`의 계산 보조가 아니라 **최종 렌더러 교체**를 포함할 수 있다. 3D 메시를 실시간으로 그릴 필요는 없으며, 기존처럼 2D 스프라이트 사각형에 재질 맵을 붙여 계산할 수 있다.

## 8. 픽셀풍 표현 시 기술 규칙

- **색상은 색으로, 데이터는 수치로 처리:** Base Color에는 팔레트 제한·디더링을 적용할 수 있지만 Normal/Depth/Height/Metallic에는 같은 색상 필터를 무작정 사용하지 않는다.
- **데이터 맵은 Non-Color/선형 값 규약 유지:** 저장·불러오기 시 감마/뷰 변환 적용 여부를 확인한다.
- **공통 픽셀 격자:** 모든 맵의 크롭·피벗·보이는 실루엣·아틀라스 위치를 일치시킨다.
- **픽셀아트 샘플링:** 필요할 때 nearest-neighbor 확대를 이용하되, 조명에 쓰는 노멀은 읽은 뒤 정규화한다.
- **회전·반전:** 이미지뿐 아니라 노멀 벡터 성분의 방향도 변환한다.
- **Height 시차 보정:** 변위된 좌표로 Base Color만 읽지 말고 해당 표면의 다른 맵도 일관되게 샘플링한다.
- **Emissive는 역할 구분:** 표면 자체의 밝기, Bloom, 인근 물체를 밝히는 조명을 각각 구현한다.
- **알파 처리:** 컷아웃과 반투명 표면을 구별한다. 여러 투명 표면을 한 픽셀의 물성값 하나로 정확하게 표현하기 어렵다.
- **HDR 선택:** 강한 반사·발광을 쓸 때는 조명값을 충분한 정밀도로 계산하고, 마지막에 톤 매핑·색 출력·픽셀풍 색 단계 조절을 검토한다.

## 9. 용량과 성능 최적화

방향별 여러 완성 조명 이미지를 저장하는 방법과 보조맵으로 런타임 조명을 계산하는 방법은 상충 관계가 있다.

```text
사전 조명 이미지량 ≈ W × H × 애니메이션 프레임 × 시점 방향 × 조명 상태 × 픽셀당 바이트
동적 재질 맵 이미지량 ≈ W × H × 애니메이션 프레임 × 시점 방향 × (맵별 픽셀당 바이트의 합)
```

예: 128×128 RGBA8 이미지를 **프레임당 4장** 보관하면 그 프레임에 필요한 비압축 픽셀 데이터는 256KiB이며, **8방향 × 12프레임**이면 총 약 **24MiB**다. 이는 아틀라스의 빈 공간·임시 버퍼·GPU 저장 형식 등을 제외한 예시다.

절감 전략:

1. 변화가 없는 재질 속성(예: Metallic=0)은 맵 대신 상수로 지정.
2. 발광하지 않는 자산의 Emissive 맵은 생략.
3. AO·Roughness·Metallic 등을 채널 패킹(예: R/G/B 각각 배치)하되 규약 명시.
4. 필요한 경우에만 Height/Depth/Position 추가.
5. 프레임 중복 제거, 방향·프레임 수 최적화, 공통 데이터 재사용.
6. 투명 여백 트리밍, 알파 경계 보존, 패딩 포함 아틀라스 빈 공간 줄이기.
7. 화면 표시 해상도에 맞는 소스 이미지 사용과 자산 캐싱.
8. GPU 렌더러에서는 지원되는 압축 텍스처를 검토. 디스크 PNG 압축과 GPU 상주 압축은 다르다.

**PNG 파일 압축률이 높아지는 것과 같은 RGBA 텍스처의 실행 중 메모리가 줄어드는 것은 다르다.** CPU 조명에는 연산·버퍼·업로드 비용, GPU 조명에는 셰이더·텍스처 샘플링·전송 및 경우에 따라 읽기 비용을 포함한다.

## 10. 단계별 프로토타입 제안

| 단계 | 목표 | 검증 기준 |
|---|---|---|
| **0. 환경 확인** | Python·Pico2D·SDL 버전, 이미지·알파·출력 경로 확인 | 실제 설치 환경의 동작 확인 및 API 제약 기록 |
| **1. 3D→2D 기본** | 단순 3D 구체와 테스트 모델을 RGBA로 변환 | 실루엣·투명 경계·피벗·방향 일치 |
| **2. 멀티패스 출력** | Base Color, Normal, AO, Emissive 등 동일 좌표로 출력 | 맵별 크롭·카메라·색공간·노멀 좌표 검증 |
| **3. 광원 하나** | CPU 또는 GPU에서 Normal 확산 조명 적용 | 빛을 움직이면 예상대로 밝은 면 변화 |
| **4. 재질 확장** | Roughness/Metallic BRDF | 금속/비금속·거칠기 차이가 일관되게 나타남 |
| **5. 요철·깊이** | 필요할 때 Height/Depth/Position 실험 | 경계·가림·시차 오류와 데이터량 측정 |
| **6. 전체 성능** | 방향·애니메이션·여러 광원·다수 개체 | CPU/GPU 계산, 픽셀 전송, 메모리, FPS 각각 기록 |

### 최소 테스트 장면

- 무광 구와 금속 구: Base Color·Metallic/Roughness 반응 비교.
- 범프 패턴의 표면: Normal의 좌표·방향 검증.
- 발광 부분: Emissive와 Bloom의 역할 구분.
- 반투명 가장자리: 알파 합성·데이터 경계 확인.
- 움직이는 방향광·점광원: 방향과 거리 계산 확인.

### 주의할 실패 사례

- 이미 조명된 RGBA를 Albedo로 사용해 조명이 두 번 적용됨.
- Normal의 Y축 또는 공간이 반대로 해석됨.
- 데이터 맵이 sRGB 변환을 받아 노멀·깊이가 왜곡됨.
- 색상만 픽셀화해 다른 맵과 위치가 어긋남.
- Alpha가 0인 바깥 픽셀의 색 때문에 경계에 검은 테두리가 생김.
- 광원·카메라가 움직이는데 Depth의 좌표 변환이 이전 시점을 사용함.
- GPU 셰이더는 빨라도 CPU 읽기·재업로드가 전체 속도를 제한함.

## 11. 선택 가이드

| 우선 목표 | 권장 시작점 |
|---|---|
| 가장 단순한 구성, Pico2D 기본 API 고수 | Blender에서 완성 렌더 + 조명 상태별 이미지 및 레이어 연출 |
| 새 런타임 패키지 없이 실제 픽셀 조명 계산 | 표준 Python 계산 + 기존 SDL 동적 텍스처 연동을 검증 |
| Pico2D 창·입력을 유지하며 실시간 재조명 | NumPy 기반 CPU 조명 + SDL 텍스처 업로드 |
| 제작 자동화/용량만 우선 개선 | Blender + 오프라인 Pillow·NumPy·아틀라스 도구, 런타임 Pico2D 유지 |
| 자유로운 재질/PBR/Height/Depth 셰이더를 중시 | ModernGL/Arcade 기반 GPU 렌더러, Pico2D 최종 출력 교체 여부 명확화 |
| 극단적인 3D 시점 변화와 다층 투과까지 정확하게 표현 | 이미지 기반 임포스터의 한계를 검토하고 실시간 3D 자체와 비용 비교 |

**권장 최초 검증 단위:** 같은 3D 원본에서 얻은 **Base Color + Normal + AO + Emissive**의 2D 스프라이트 한 세트와 움직이는 광원 한 개. 먼저 Pico2D/SDL의 출력 연결이 실제로 가능한지 확인한 뒤, CPU 계산과 GPU 계산을 동일한 에셋·화면 크기에서 비교한다. Metallic/Roughness는 그다음, Height/Depth는 구체적인 시차·가림 요구가 있을 때 추가한다.

---

## 12. 참고 문서

> 아래는 기술 개념 및 API를 확인하기 위한 공식 문서·원전 링크다. 라이브러리별 정확한 함수와 지원 여부는 **사용할 설치 버전**으로 다시 검증해야 한다.

- [Pico2D — PyPI 배포 정보](https://pypi.org/project/pico2d/)
- [Blender — Render Passes](https://docs.blender.org/manual/en/latest/render/layers/passes.html)
- [Blender — Shader AOV](https://docs.blender.org/manual/en/3.6/render/shader_nodes/output/aov.html)
- [Blender — Cycles Baking](https://docs.blender.org/manual/en/latest/render/cycles/baking.html)
- [Blender — Color Management](https://docs.blender.org/manual/en/4.0/render/color_management.html)
- [Blender — File Output Node](https://docs.blender.org/manual/en/latest/compositing/types/output/file_output.html)
- [Blender — Principled BSDF](https://docs.blender.org/manual/en/4.0/render/shader_nodes/shader/principled.html)
- [SDL2 — Texture Update](https://wiki.libsdl.org/SDL2/SDL_UpdateTexture)
- [SDL2 — Texture Lock](https://wiki.libsdl.org/SDL2/SDL_LockTexture)
- [SDL2 — Blend Mode](https://wiki.libsdl.org/SDL2/SDL_BlendMode)
- [NumPy — Broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting)
- [Pillow — Image Reference](https://pillow.readthedocs.io/en/stable/reference/Image.html)
- [ModernGL — Context API](https://moderngl.readthedocs.io/en/stable/reference/context.html)
- [ModernGL — Window Integration](https://moderngl.readthedocs.io/en/stable/the_guide/functionality_expansion/window_using.html)
- [Arcade — Normal Mapping Example](https://api.arcade.academy/en/stable/example_code/normal_mapping.html)
- [Arcade — Light Example](https://api.arcade.academy/en/stable/example_code/light_demo.html)
- [Khronos — glTF 2.0 Specification (Material)](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc)
- [Google Filament — Physically Based Rendering](https://google.github.io/filament/main/filament.html)
- [NVIDIA GPU Gems 2 — Pixel Displacement Mapping](https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-8-pixel-displacement-mapping-distance-functions)
- [NVIDIA GPU Gems 3 — True Impostors](https://developer.nvidia.com/gpugems/gpugems3/part-iv-image-effects/chapter-21-true-impostors)
- [Polynomial Texture Maps — Malzbender et al.](https://www.cs.jhu.edu/~misha/ReadingSeminar/Papers/Malzbender01.pdf)
