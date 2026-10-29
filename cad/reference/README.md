# CAD 레퍼런스 (Pollen Robotics 원본)

이 폴더는 [`pollen-robotics/microduck_rl`](https://github.com/pollen-robotics/microduck_rl)
`develop` 브랜치(commit `bae39f5`, 2026-10-27)의 `src/mjlab_microduck/robot/`을 **수정 없이** 복사한 것이다.
재설계 결과물은 `../redesign/`에 둔다. 이 폴더의 파일은 고치지 않는다(원본 비교 기준).

## 내용

| 경로 | 내용 |
|---|---|
| `microduck/robot_*.xml` | MJCF 로봇 모델 (walk, groundcontact, rollers, allcollisions, *_backlash) |
| `microduck/scene*.xml` | 바닥·키프레임(INIT, STAND, SIT, FOLD) 포함 장면 |
| `microduck/joints_properties.xml` | 액추에이터 클래스 (XL330 PD 근사값) |
| `microduck/sensors.xml`, `additional.xml` | IMU·카메라 사이트, 추가 요소 |
| `microduck/config_mjcf_*.json` | onshape-to-robot 내보내기 설정 (**원본 Onshape URL 포함**) |
| `microduck/assets/*.stl` | 부품 메시 43종 (시뮬레이션용으로 단순화됨) |
| `microduck/assets/*.part` | 부품별 Onshape 메타데이터 (documentId, partId) |
| `xl330_test_bench/` | 서보 1개 식별(BAM)용 테스트벤치 모델 |
| `parts.csv` | 부품 치수·부피·수량·재질 추정표 (`../tools/parts_table.py`로 생성) |

## 원본 Onshape 문서

```
https://cad.onshape.com/documents/804927696f06d877f3f1803e/w/5b75db19292e71970de02dee/e/ef6e972847fec8d82570b35e
(테스트벤치) https://cad.onshape.com/documents/804927696f06d877f3f1803e/w/3df6f6a8dcea50fb5658e3c0/e/54c1186243f1b4db10e4bd59
```
공개 여부는 확인하지 못했다. Onshape에 로그인해서 열어 보고, 열리면 "Make a copy"로 복사해 쓰는 것이 가장 좋다.

## 주의

- STL은 `simplify_stls: true`로 내보낸 **시뮬레이션용 메시**다. 나사 구멍, 공차, 인서트 자리가
  제작용으로 정확하다는 보장이 없다. 출력 전 확인하고, 서보 장착부는 ROBOTIS XL330 공식 도면으로 재모델링 권장.
- `pcb__raspberry_pi_zero_2_w`는 자리표시자다. 실물은 같은 65×30 mm 폼팩터의 Radxa Zero 3W.
- `np_f970`은 NP-F970 크기의 배터리 외형이고, 제품은 NP-F550을 쓴다 (길이가 더 짧음).
- `ankle_*_v1`은 롤러 모델용 발목 변형이다.

## 라이선스

- `*.stl` 메시: **CC BY-NC-SA 4.0**, © Pollen Robotics. 비상업 용도만, 출처 표기, 수정본도 같은 라이선스.
  자세한 내용은 [`LICENSE-MODELS.md`](LICENSE-MODELS.md).
- MJCF(`.xml`), 설정(`.json`), `.part` 메타데이터: Apache-2.0 (© Pollen Robotics).

수정 사항: 없음 (원본 그대로 복사).
