#imports 
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from dotenv import load_dotenv
import os
import google.generativeai as genai 
import json
import logging 

logging.basicConfig(level=logging.INFO)

#load gemini API key 
load_dotenv()
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# for m in genai.list_models():
#     print(m.name)
# Initialize Gemini model
model = genai.GenerativeModel("models/gemini-2.5-flash")
DATABASE_URL= os.getenv("DATABASE_URL")
FRONTEND_URL= os.getenv("FRONTEND_URL", "http://localhost:5173")

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# DB model
class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, default="")
    completed = Column(Boolean, default=False)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic schemas
class Task(BaseModel):
    title: str
    description: str = ""
    completed: bool = False

class TaskDB(Task):
    id: int
    class Config:
        from_attributes = True

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://task-manager.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/tasks", response_model=List[TaskDB])
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(TaskModel).all()
    return tasks

@app.post("/tasks", response_model=TaskDB)
def create_task(task: Task, db: Session = Depends(get_db)):
    db_task = TaskModel(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.put("/tasks/{task_id}", response_model=TaskDB)
def update_task(task_id: int, task: Task, db: Session = Depends(get_db)):
    db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.title = task.title
    db_task.description = task.description
    db_task.completed = task.completed
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"message": "Task deleted"}


#LLM based recommendations 
@app.get("/recommendations")
def get_task_recommendations(db: Session = Depends(get_db)):
    try:
        logging.info("Fetching tasks for recommendations")
        tasks = db.query(TaskModel).all()

        if not tasks:
            logging.warning("No tasks found for recommendations")
            return {"message": "No tasks available for recommendations."}

        task_summary = "\n".join(
            [f"- {t.title} (Completed: {t.completed})" for t in tasks]
        )
        logging.info(f"sending {len(tasks)} tasks to gemini")
        response = model.generate_content(
            f"""You are a helpful task management assistant.
             Here are my current tasks:{task_summary}
             Please provide recommendations on which tasks to prioritize and next steps. 
             Format your response clearly: 
             - Use numbered tasks. 
             - Use bold text for priorities and subheadings. 
             - Include bullet points for actionable next steps. 
             - Add a short final recommendation. Return as plain text with line breaks so it's easy to read.
             Do Not repeat instructions 
             Only return answers 
             """
        )
        logging.info("Recommendations generated successfully")
        return {"recommendation": response.text}
    except Exception as e:
        logging.error(f"Error in generating recommendations {str(e)}")
        if "quota exceeded" in str(e).lower():
            return {"recommendation": "You exceeded your limit to generate recommendations. Try again tomorrow!"}
        else:
            raise HTTPException(status_code=500, detail=str(e))
       
#creating a task using LLM 

class TaskPrompt(BaseModel):
    prompt: str

@app.post("/generate_task")
def generate_task(task_prompt: TaskPrompt, db: Session = Depends(get_db)):
    try:
        logging.info("Received task prompt:{task_prompt.prompt}")
        prompt = f"""
        Create a task from this request: {task_prompt.prompt}

        Respond ONLY in valid JSON:
        {{
            "title": "Task Title",
            "description": "Task Description"
        }}
        No markdown.
        No extra text.
        """
        logging.info("Sending prompt to gemini")
        # Call LLM
        response = model.generate_content(prompt)
        if not response.text:
            logging.error("Empty response from gemini")
            raise HTTPException(status_code=500, detail="Empty response from Gemini API")

        content_str = response.text.strip()

        if content_str.startswith("```json"):
            content_str = (
                content_str
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        task_data = json.loads(content_str)
        logging.info(f"Parsed task data:{task_data}")
        db_task = TaskModel(
            title=task_data["title"],
            description=task_data["description"],
            completed=False
        )

        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        logging.info("Task created successffully with ID:{db_task.id}")
        return db_task

    except Exception as e:
        logging.error(f"Error in task generation:{str(e)}")
        if "quota exceeded" in str(e).lower():
            raise HTTPException(status_code=429, detail="You exceeded your limit to generate tasks with AI. Try again tomorrow!")
        else:
            raise HTTPException(status_code=500, detail=str(e))