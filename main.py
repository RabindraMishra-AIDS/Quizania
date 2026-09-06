import json
import os
import random
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="Hinglish Engineering Quiz")
app.mount("/static", StaticFiles(directory="static"), name="static")

TOPICS = [
    ("Artificial intelligence", "Systems that perform tasks requiring human-like reasoning, learning, or perception."),
    ("Machine learning", "A branch of AI that learns patterns from data to make predictions or decisions."),
    ("Virtualization", "Making multiple isolated computing environments run on one physical machine."),
    ("Cloud computing", "Delivering computing resources over the internet on demand."),
    ("Emulator", "Software that imitates the behavior of another system or device."),
    ("Kernel module", "A piece of code that can be loaded into the Linux kernel to extend its capabilities."),
    ("RHEL Linux", "Red Hat Enterprise Linux, a supported enterprise operating system used in production environments."),
    ("Compiling", "Translating source code into machine-readable code."),
    ("Cross-compiling", "Building code on one platform for a different target platform."),
    ("Binary", "A base-two representation used by computers."),
    ("C language", "A foundational compiled programming language."),
    ("Virtual machine", "A software-defined computer running its own operating system."),
    ("Container", "A lightweight package that bundles an application and its dependencies."),
    ("Load balancing", "Distributing traffic or work across multiple servers."),
    ("5G", "The fifth generation of cellular-network technology."),
    ("GSM", "A global cellular standard that uses SIM-based subscriber identity and time-division radio access."),
    ("CDMA", "A cellular access method that separates users through distinct spreading codes."),
    ("Packet switching", "Sending data as addressed packets that can travel independently across a network."),
    ("Kernel interrupt", "A signal that temporarily pauses normal CPU execution so the system can handle an event."),
    ("Cell tower", "A radio site that provides wireless coverage and connects mobile devices to a network."),
    ("Base station controller", "A telecom network component that manages radio resources and multiple base stations."),
    ("eNodeB", "The LTE radio access network node that connects mobile devices to the evolved packet core."),
    ("VoIP", "Voice over Internet Protocol, which carries voice calls over IP networks."),
    ("LTE", "A 4G mobile broadband standard designed for high-speed packet-based communication."),
    ("Latency", "The delay before data begins to transfer."),
    ("Bandwidth", "The maximum amount of data a connection can carry in a period."),
    ("Kubernetes", "A system for managing containerized applications."),
    ("DNS", "The system that translates human-readable domain names into IP addresses."),
    ("TCP", "A reliable, connection-oriented transport protocol."),
    ("UDP", "A connectionless transport protocol optimized for speed and low overhead."),
    ("HTTP", "The application protocol used to transfer web resources."),
    ("API gateway", "A service that manages, routes, and protects requests to backend APIs."),
    ("Message queue", "A buffer that lets services communicate asynchronously through messages."),
    ("Database replication", "Copying data between database instances for availability or scale."),
    ("Observability", "Understanding system behavior through logs, metrics, and traces."),
    ("CI/CD", "Automating software integration, testing, and delivery pipelines."),
    ("Microservices", "An architecture that splits an application into independently deployable services."),
    ("Encryption", "Transforming data so only authorized parties can read it."),
    ("Authentication", "Verifying the identity of a user or service."),
    ("Firewall", "A security control that filters network traffic according to rules."),
    ("Edge computing", "Processing data near its source instead of sending everything to a central cloud."),
    ("Autoscaling", "Automatically adjusting compute capacity as demand changes."),
]

HINGLISH_OPENERS = [
    "Agar system ko smoothly chalana hai, toh batao:",
    "Chalo is technical situation ko simple Hinglish mein samjho:",
    "Team ke saamne yeh problem aa gayi hai. Best answer kya hoga:",
    "Socho production environment mein yeh case ho gaya. Kaunsa concept fit hota hai:",
    "Seedhi si baat hai, is scenario mein kaunsi technology use hogi:",
    "Thoda practical socho: is engineering challenge ka solution kya hai:",
    "Ab batao, network aur system ke beech yahan kya ho raha hai:",
]


class QuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    answer: str
    explanation: str


class QuizPayload(BaseModel):
    questions: list[QuizQuestion] = Field(min_length=7, max_length=7)
    source: str


class AnswerSubmission(BaseModel):
    answers: list[str]
    questions: list[QuizQuestion]


def fallback_quiz() -> list[QuizQuestion]:
    ai_topics = [topic for topic in TOPICS if topic[0] in {"Artificial intelligence", "Machine learning"}]
    other_topics = [topic for topic in TOPICS if topic not in ai_topics]
    required_topics = [topic for topic in other_topics if topic[0] in {"Emulator", "Kernel module", "RHEL Linux"}]
    remaining_topics = [topic for topic in other_topics if topic not in required_topics]
    selected = random.sample(ai_topics, 2) + required_topics + random.sample(remaining_topics, 2)
    random.shuffle(selected)
    quiz = []
    for index, (term, explanation) in enumerate(selected):
        wrong = [name for name, _ in random.sample([t for t in TOPICS if t[0] != term], 3)]
        options = wrong + [term]
        random.shuffle(options)
        opener = HINGLISH_OPENERS[index]
        quiz.append(QuizQuestion(
            question=f'{opener} {explanation}',
            options=options,
            answer=term,
            explanation=f"{term}: {explanation}",
        ))
    return quiz


def extract_json(content: str) -> Any:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    if not content.startswith(("[", "{")):
        array_start = content.find("[")
        object_start = content.find("{")
        starts = [index for index in (array_start, object_start) if index != -1]
        if not starts:
            raise ValueError("The LLM response did not contain JSON")
        start = min(starts)
        end = max(content.rfind("]"), content.rfind("}"))
        if end < start:
            raise ValueError("The LLM response did not contain complete JSON")
        content = content[start:end + 1]
    return json.loads(content)


async def ai_quiz() -> list[QuizQuestion]:
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise RuntimeError("No LLM API key configured")
    prompt = """Create exactly 7 multiple-choice questions for an Indian cloud, AI, telecom, Linux, and software engineering quiz.
Use a general conversational Hinglish style: natural Hindi-English phrasing, practical engineering situations, and simple explanations. Do not use Bollywood themes, film dialogue, celebrity references, dramatic cinema scenes, or fictional character voices. Keep every technical clue accurate and easy to understand.
Exactly 2 questions must have one of these exact correct answers: "Artificial intelligence" or "Machine learning". Include exactly one question whose exact correct answer is "Emulator", exactly one whose exact correct answer is "Kernel module", and exactly one whose exact correct answer is "RHEL Linux". Use the other two questions for different concepts from this broad pool: cloud computing, virtualization, virtual machine, container, Kubernetes, 5G, GSM, CDMA, packet switching, kernel interrupt, cell tower, base station controller, eNodeB, VoIP, LTE, latency, bandwidth, load balancing, DNS, TCP, UDP, HTTP, API gateway, message queue, database replication, observability, CI/CD, microservices, encryption, authentication, firewall, edge computing, or autoscaling.
Do not ask the same concept twice or merely rephrase another question. Each question must test a different technical concept and use a different question style, such as scenario diagnosis, best tool choice, comparison, troubleshooting, or architecture decision. Each question must have exactly 4 distinct options, exactly 1 correct answer, and a concise educational explanation. The answer field must exactly match the one correct option. Return ONLY a JSON object with a "questions" array containing exactly 7 objects using these fields: question, options, answer, explanation."""
    base = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "temperature": 0.3, "max_tokens": 4000, "reasoning_effort": "low", "messages": [{"role": "user", "content": prompt}]},
        )
        response.raise_for_status()
    data = extract_json(response.json()["choices"][0]["message"]["content"])
    if isinstance(data, dict):
        data = data.get("questions")
    if not isinstance(data, list):
        raise ValueError("The LLM response did not contain a questions array")
    questions = [QuizQuestion.model_validate(item) for item in data]
    answers = [q.answer for q in questions]
    ai_answers = {"Artificial intelligence", "Machine learning"}
    required_answers = {"Emulator", "Kernel module", "RHEL Linux"}
    if (
        len(questions) != 7
        or len(set(answers)) != 7
        or len(ai_answers.intersection(answers)) != 2
        or not required_answers.issubset(answers)
        or any(q.answer not in q.options or len(set(q.options)) != 4 for q in questions)
    ):
        raise ValueError("The LLM returned an invalid quiz")
    return questions


@app.get("/", response_class=FileResponse)
async def home():
    return FileResponse(Path("static/index.html"))


@app.get("/api/quiz", response_model=QuizPayload)
async def get_quiz():
    try:
        return QuizPayload(questions=await ai_quiz(), source="AI-generated")
    except Exception:
        return QuizPayload(questions=fallback_quiz(), source="Fresh local quiz (AI generation unavailable)")


@app.post("/api/score")
async def score_quiz(submission: AnswerSubmission):
    if len(submission.answers) != len(submission.questions):
        raise HTTPException(400, "Answers do not match questions")
    results = []
    for question, selected in zip(submission.questions, submission.answers):
        results.append({"correct": selected == question.answer, "answer": question.answer, "explanation": question.explanation})
    return {"score": sum(item["correct"] for item in results), "total": len(results), "results": results}
