# 톡토기 구조도 생성

프로젝트 루트에서 기존 런타임 의존성을 설치한 Python으로 실행한다.

```powershell
python document/tools/architecture/build_atlas.py
python document/tools/architecture/verify_atlas.py
node document/tools/architecture/verify_interactions.cjs
```

생성기는 프로젝트의 모션 HTML, 두 런타임 ZIP, 검증 결과, 모듈 소스를 읽는다. Blender나 참고 레이아웃 문서의 원래 경로는 필요하지 않다. 레이아웃 파일은 atlas.template.html과 atlas.css다. document 폴더에 생성된 ToktogiProjectArchitecture.html은 단독으로 열린다.

[통합 게임 기획 명세](../../markdown/001_toktogi_game_design_spec.md#atlas-sources)의 구조도 갱신 계약에서 9개 HTML 섹션의 원본을 지정한다. 링크의 표시 이름은 자유롭게 바꿀 수 있다. Markdown의 특정 절을 링크할 때는 해당 절의 2단계 제목 앞에 `<a id="절-ID"></a>`를 둔다.

호출 순서와 객체 관계는 프레임워크 명세에서 읽는다. 단축키는 상태 머신의 현행 입력표에서 읽고, 상태 상세와 요약표는 같은 Mermaid 전이에서 만든다. 모션 수와 대표 재생은 모션 HTML 데이터에서, 재질 적용 상태는 셰이더 명세에서 읽는다. Python 파일 구조의 import와 정의 줄 번호는 현재 소스에서 추출한다. 파일 상세에는 `#files/game.py`처럼 바로 연결할 수 있다.

명세서 지도는 하위 제목마다 카드 하나를 만든다. 카드 항목마다 상대 Markdown 링크와 설명을 한 줄에 둔다. 검증·근거 섹션은 현재 프로젝트 소스의 결과를 표시한다. 배포 ZIP은 배포 시점의 자료로 연결한다.
