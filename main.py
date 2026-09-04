import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="CareLoop API", description="복약 및 재활 운동 데이터 처리 API")

# 1. 데이터 모델 정의
class PatientCareRecord(BaseModel):
    patient_id: str
    medication_taken: bool          # 복약 여부
    exercise_completed: bool        # 재활 운동 수행 여부
    pain_score: int                 # 통증 점수 (0 ~ 10)
    has_warning_symptoms: bool     # 발열/진물 등 이상 증상 여부
    notes: Optional[str] = None     # 특이사항 및 메모

# 메모리 내 데이터 저장소 (프로토타입용)
db_records: List[PatientCareRecord] = []

# 2. 백엔드 API 엔드포인트
@app.post("/api/record")
def create_record(record: PatientCareRecord):
    """환자의 일일 복약 및 재활 기록을 저장하고 위험도를 분석합니다."""
    db_records.append(record)
    
    alert_triggered = False
    alert_message = "정상적으로 기록되었습니다. 내일도 재활을 이어가세요!"
    
    if record.has_warning_symptoms or record.pain_score >= 7:
        alert_triggered = True
        alert_message = "⚠️ 주의: 통증이 심하거나 부작용 징후가 있습니다. 무리한 운동을 중단하고 병원 진료를 받으세요."
    elif record.pain_score >= 4:
        alert_message = "⚡ 참고: 통증 수치가 약간 높습니다. 운동 강도를 낮추고 경과를 관찰하세요."

    return {
        "status": "success",
        "alert": alert_triggered,
        "message": alert_message,
        "data": record
    }

@app.get("/api/doctor-summary")
def get_doctor_summary():
    """의사가 진료 시 한눈에 확인하는 요약 데이터 리포트 API"""
    if not db_records:
        return {"message": "기록된 데이터가 없습니다."}
    
    total_days = len(db_records)
    med_compliance = sum(1 for r in db_records if r.medication_taken) / total_days * 100
    ex_compliance = sum(1 for r in db_records if r.exercise_completed) / total_days * 100
    avg_pain = sum(r.pain_score for r in db_records) / total_days
    warnings_count = sum(1 for r in db_records if r.has_warning_symptoms or r.pain_score >= 7)

    return {
        "total_recorded_days": total_days,
        "medication_compliance_rate": f"{med_compliance:.1f}%",
        "exercise_compliance_rate": f"{ex_compliance:.1f}%",
        "average_pain_score": round(avg_pain, 1),
        "high_risk_event_count": warnings_count,
        "recent_records": db_records[-5:]
    }

# 3. 프론트엔드 웹 화면 (HTML/JS)
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>케어루프 (CareLoop) - 프로토타입</title>
    <style>
        :root {
            --bg: #FFFFFF;
            --ink: #000000;
            --ink-soft: #555555;
            --fill-soft: #F2F2F2;
        }
        body {
            font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
            margin: 0;
            padding: 40px 20px;
            background: var(--bg);
            color: var(--ink);
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            border: 2px solid var(--ink);
            padding: 30px;
        }
        h1 {
            margin-top: 0;
            font-size: 28px;
            border-bottom: 2px solid var(--ink);
            padding-bottom: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            font-weight: bold;
            margin-bottom: 8px;
        }
        input[type="number"], textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid var(--ink);
            box-sizing: border-box;
            font-size: 14px;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .checkbox-group input {
            width: 18px;
            height: 18px;
        }
        button {
            width: 100%;
            background: var(--ink);
            color: #FFF;
            padding: 12px;
            border: none;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover {
            background: var(--ink-soft);
        }
        .result-box {
            margin-top: 25px;
            padding: 15px;
            border: 1px solid var(--ink);
            background: var(--fill-soft);
            display: none;
        }
        .alert-warning {
            border-color: #000;
            font-weight: bold;
        }
    </style>
</head>
<body>

<div class="container">
    <h1>케어루프 (CareLoop)</h1>
    <p style="color: var(--ink-soft);">오늘의 복약과 재활 운동 상태를 기록해 주세요.</p>

    <form id="careForm">
        <div class="form-group checkbox-group">
            <input type="checkbox" id="medicationTaken" checked>
            <label for="medicationTaken" style="margin-bottom:0;">오늘 약을 처방대로 복용했나요?</label>
        </div>

        <div class="form-group checkbox-group">
            <input type="checkbox" id="exerciseCompleted" checked>
            <label for="exerciseCompleted" style="margin-bottom:0;">오늘 목표한 재활 운동을 수행했나요?</label>
        </div>

        <div class="form-group">
            <label for="painScore">오늘 느끼는 통증 점수 (0: 통증 없음 ~ 10:극심함)</label>
            <input type="number" id="painScore" min="0" max="10" value="2" required>
        </div>

        <div class="form-group checkbox-group">
            <input type="checkbox" id="warningSymptoms">
            <label for="warningSymptoms" style="margin-bottom:0;">수술 부위 진물, 발열 등 이상 징후가 있나요?</label>
        </div>

        <div class="form-group">
            <label for="notes">특이사항 및 메모</label>
            <textarea id="notes" rows="3" placeholder="운동 시 느낀 점이나 특이한 증상을 적어주세요."></textarea>
        </div>

        <button type="button" onclick="submitRecord()">오늘 기록 등록하기</button>
    </form>

    <div id="resultBox" class="result-box">
        <div id="resultMessage"></div>
    </div>
</div>

<script>
async function submitRecord() {
    const payload = {
        patient_id: "PATIENT_001",
        medication_taken: document.getElementById('medicationTaken').checked,
        exercise_completed: document.getElementById('exerciseCompleted').checked,
        pain_score: parseInt(document.getElementById('painScore').value),
        has_warning_symptoms: document.getElementById('warningSymptoms').checked,
        notes: document.getElementById('notes').value
    };

    try {
        const response = await fetch('/api/record', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        const resultBox = document.getElementById('resultBox');
        const resultMessage = document.getElementById('resultMessage');

        resultBox.style.display = 'block';
        resultMessage.innerText = result.message;

        if (result.alert) {
            resultBox.className = "result-box alert-warning";
        } else {
            resultBox.className = "result-box";
        }

    } catch (error) {
        alert("기록 전송 중 오류가 발생했습니다.");
    }
}
</script>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return HTML_LAYOUT

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
