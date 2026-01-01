# groupby

## 프로그래머스 부서별 평균 연봉 조회하기

### 문제

HR_DEPARTMENT 테이블의 구조는 다음과 같으며 DEPT_ID, DEPT_NAME_KR, DEPT_NAME_EN, LOCATION은 각각 부서 ID, 국문 부서명, 영문 부서명, 부서 위치를 의미

HR_EMPLOYEES 테이블은 회사의 사원 정보를 담은 테이블입니다. HR_EMPLOYEES 테이블의 구조는 다음과 같으며 EMP_NO, EMP_NAME, DEPT_ID, POSITION, EMAIL, COMP_TEL, HIRE_DATE, SAL은 각각 사번, 성명, 부서 ID, 직책, 이메일, 전화번호, 입사일, 연봉을 의미

HR_DEPARTMENT와 HR_EMPLOYEES 테이블을 이용해 부서별 평균 연봉을 조회. 부서별로 부서 ID, 영문 부서명, 평균 연봉을 조회하는 SQL문을 작성

평균연봉은 소수점 첫째 자리에서 반올림하고 컬럼명은 AVG_SAL로. 결과는 부서별 평균 연봉을 기준으로 내림차순 정렬

### 내 풀이

```sql
select dept.dept_id, dept.dept_name_en, ROUND(avg(emp.sal), 0) as AVG_SAL from HR_DEPARTMENT dept join HR_EMPLOYEES emp on dept.dept_id = emp.dept_id
group by dept.dept_id, dept.dept_name_en order by AVG_SAL desc;
```

### 해답

```sql
select dept.dept_id, dept.dept_name_en, emp.AVG_SAL from HR_DEPARTMENT dept 
join (
    select dept_id, ROUND(avg(coalesce(sal)), 0) as AVG_SAL
    from HR_EMPLOYEES 
    group by dept_id
) emp on emp.dept_id = dept.dept_id
order by emp.AVG_SAL desc;
```

### note

* emp 로우의 갯수가 많을것으로 예상해 집계를 먼저하고 조인하는 방식으로 하면 EMPLOYEES 테이블 한 번만 스캔 + 집계 결과가 작어져서 조인 비용 감소
* 데이터에 null이 들어갈수 있으니 coalesce 처리
* ORDER BY는 가독성을 위해 별칭 사용
