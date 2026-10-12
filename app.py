
from flask import Flask, request, jsonify
from functools import wraps

app = Flask(__name__)

# ----------------------------------
# SAMPLE DATABASE (IN-MEMORY STORAGE)
# ----------------------------------

candidates = {
    "student1": {
        "password": "exam123",
        "candidate_id": "C001"
    }
}

tokens = {}

exam = {
    "examId": 101,
    "title": "Python Examination",
    "durationMinutes": 60,
    "totalQuestions": 3,
    "status": "AVAILABLE"
}

questions = [
    {
        "questionId": 1,
        "question": "Which language is used with Flask?",
        "options": ["Python", "Java", "C", "HTML"],
        "correctAnswer": "Python",
        "marks": 1
    },
    {
        "questionId": 2,
        "question": "Which data type stores True or False?",
        "options": ["String", "Boolean", "List", "Integer"],
        "correctAnswer": "Boolean",
        "marks": 1
    },
    {
        "questionId": 3,
        "question": "Which HTTP method retrieves data?",
        "options": ["POST", "DELETE", "GET", "PATCH"],
        "correctAnswer": "GET",
        "marks": 1
    }
]

# Key: (candidate_id, question_id)
answers = {}

# Key: candidate_id
submissions = {}
results = {}


# ----------------------------------
# AUTHENTICATION
# ----------------------------------

def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Login required. Send a Bearer token."
            }), 401

        token = auth_header.split(" ", 1)[1]
        candidate_id = tokens.get(token)

        if not candidate_id:
            return jsonify({
                "error": "Invalid token"
            }), 401

        request.candidate_id = candidate_id
        return func(*args, **kwargs)

    return wrapper


# ----------------------------------
# API 1: LOGIN
# ----------------------------------

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")

    user = candidates.get(username)

    if not user or user["password"] != password:
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    # Demo token; use secure token generation in production
    token = "demo-" + user["candidate_id"]
    tokens[token] = user["candidate_id"]

    return jsonify({
        "message": "Login successful",
        "candidateId": user["candidate_id"],
        "token": token
    }), 200


# ----------------------------------
# API 2: GET EXAM DETAILS
# ----------------------------------

@app.route("/api/exams/<int:exam_id>", methods=["GET"])
@require_login
def get_exam(exam_id):
    if exam_id != exam["examId"]:
        return jsonify({"error": "Exam not found"}), 404

    return jsonify({
        "examId": exam["examId"],
        "title": exam["title"],
        "durationMinutes": exam["durationMinutes"],
        "totalQuestions": exam["totalQuestions"],
        "status": (
            "SUBMITTED"
            if request.candidate_id in submissions
            else exam["status"]
        )
    }), 200


# ----------------------------------
# API 3: GET QUESTIONS
# ----------------------------------

@app.route("/api/exams/<int:exam_id>/questions",
           methods=["GET"])
@require_login
def get_questions(exam_id):
    if exam_id != exam["examId"]:
        return jsonify({"error": "Exam not found"}), 404

    if request.candidate_id in submissions:
        return jsonify({
            "error": "Exam already submitted"
        }), 409

    # Never send correct answers to candidates
    public_questions = [
        {
            "questionId": q["questionId"],
            "question": q["question"],
            "options": q["options"],
            "marks": q["marks"]
        }
        for q in questions
    ]

    return jsonify({
        "examId": exam_id,
        "questions": public_questions
    }), 200


# ----------------------------------
# API 4: SUBMIT ANSWER
# ----------------------------------

@app.route("/api/exams/<int:exam_id>/answers",
           methods=["POST"])
@require_login
def submit_answer(exam_id):
    if exam_id != exam["examId"]:
        return jsonify({"error": "Exam not found"}), 404

    candidate_id = request.candidate_id

    if candidate_id in submissions:
        return jsonify({
            "error": "Exam already submitted"
        }), 409

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Request body must be a JSON object"
        }), 400

    question_id = data.get("questionId")
    answer = data.get("answer")

    if question_id is None or answer is None:
        return jsonify({
            "error": "questionId and answer are required"
        }), 400

    if not isinstance(question_id, int) or isinstance(question_id, bool):
        return jsonify({
            "error": "questionId must be an integer"
        }), 400

    question = next(
        (q for q in questions
         if q["questionId"] == question_id),
        None
    )

    if question is None:
        return jsonify({
            "error": "Question not found"
        }), 404

    if answer not in question["options"]:
        return jsonify({
            "error": "Answer must match one of the options"
        }), 400

    # Save or update the candidate's answer
    answers[(candidate_id, question_id)] = answer

    return jsonify({
        "message": "Answer saved successfully",
        "examId": exam_id,
        "questionId": question_id,
        "status": "SAVED"
    }), 200


# ----------------------------------
# API 5: SUBMIT EXAM
# ----------------------------------

@app.route("/api/exams/<int:exam_id>/submit",
           methods=["POST"])
@require_login
def submit_exam(exam_id):
    if exam_id != exam["examId"]:
        return jsonify({"error": "Exam not found"}), 404

    candidate_id = request.candidate_id

    if candidate_id in submissions:
        return jsonify({
            "error": "Exam already submitted"
        }), 409

    # Record final submission
    submissions[candidate_id] = {
        "examId": exam_id,
        "status": "SUBMITTED"
    }

    # Simple automatic evaluation
    score = 0
    answered_count = 0

    for question in questions:
        key = (candidate_id, question["questionId"])

        if key in answers:
            answered_count += 1

            if answers[key] == question["correctAnswer"]:
                score += question["marks"]

    results[candidate_id] = {
        "examId": exam_id,
        "candidateId": candidate_id,
        "score": score,
        "totalMarks": sum(q["marks"] for q in questions),
        "answeredQuestions": answered_count,
        "status": "PROCESSED"
    }

    return jsonify({
        "message": "Exam submitted successfully",
        "examId": exam_id,
        "status": "SUBMITTED",
        "resultStatus": "PROCESSED"
    }), 200


# ----------------------------------
# API 6: GET EXAM STATUS
# ----------------------------------

@app.route("/api/exams/<int:exam_id>/status",
           methods=["GET"])
@require_login
def get_exam_status(exam_id):
    if exam_id != exam["examId"]:
        return jsonify({"error": "Exam not found"}), 404

    candidate_id = request.candidate_id

    status = (
        "SUBMITTED"
        if candidate_id in submissions
        else "IN_PROGRESS"
    )

    return jsonify({
        "examId": exam_id,
        "candidateId": candidate_id,
        "status": status
    }), 200


# ----------------------------------
# API 7: GET EXAM RESULT
# ----------------------------------

@app.route("/api/exams/<int:exam_id>/results/me",
           methods=["GET"])
@require_login
def get_exam_result(exam_id):
    if exam_id != exam["examId"]:
        return jsonify({"error": "Exam not found"}), 404

    candidate_id = request.candidate_id

    if candidate_id not in submissions:
        return jsonify({
            "error": "Submit the exam before checking results"
        }), 409

    return jsonify(results[candidate_id]), 200


# ----------------------------------
# RUN SERVER
# ----------------------------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
