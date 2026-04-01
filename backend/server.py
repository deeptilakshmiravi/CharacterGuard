from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from utils.file_io import (
    parse_upload,
    parse_dataset_sample,
    load_run_result,
    list_saved_runs,
    _run_result_to_dict,
)
from runner import Runner, RunResult

# import logging

# Import routers
# from backend.routes import run_tests, results, comparison

# --------------------------------------------------
# Logging setup
# --------------------------------------------------
# logging.basicConfig(
    # level=logging.INFO,
    # format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
# )
# logger = logging.getLogger(__name__)


app = FastAPI(
    title="CharacterGuard API",
    description="API for testing and evaluating AI character robustness",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    # change this to production url later
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "CharacterGuard API is running",
        "version": "1.0.0"
    }

# ---------------------------------------------------------------------------
# POST /run/production
# ---------------------------------------------------------------------------
 
@app.post("/run/production")
async def run_production(
    description: str = Form(..., description="Character persona/description text"),
    conversations: UploadFile = File(..., description="CSV file with columns: question, answer"),
):
    """
    Trigger a production mode safety evaluation run.
 
    Accepts:
        description   : character persona as a form field (plain text)
        conversations : CSV file upload with columns: question, answer
 
    Returns:
        Full RunResult as JSON
    """
    #logger.info("Received production run request")
 
    # Validate file type
    if not conversations.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Conversations file must be a CSV. Please upload a .csv file."
        )
 
    try:
        # Parse upload into TranscriptRows
        rows = parse_upload(
            description=description,
            csv_file=conversations.file,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
 
    if not rows:
        raise HTTPException(
            status_code=422,
            detail="No valid rows found in the uploaded CSV. "
                   "Check that your file has 'question' and 'answer' columns."
        )
 
    try:
        runner = Runner(mode="production")
        result: RunResult = runner.run(rows)
    except Exception as e:
        #logger.error(f"Production run failed: {e}")
        raise HTTPException(status_code=500, detail=f"Run failed: {str(e)}")
 
    return _run_result_to_dict(result)
 
 
# ---------------------------------------------------------------------------
# POST /run/validation
# ---------------------------------------------------------------------------
 
@app.post("/run/validation")
async def run_validation(
    dataset: UploadFile = File(
        ...,
        description="Validation CSV from the research dataset with columns: "
                    "description, question, answer, judge_score, judge_category, NSFW"
    ),
):
    """
    Trigger a validation mode run against the research dataset sample.
 
    Accepts:
        dataset : CSV file upload (validation_sample.csv from the research dataset)
 
    Returns:
        Full RunResult as JSON, including ground truth comparison metrics
        (ground_truth_agreement_rate, category_match_rate)
    """
    #logger.info("Received validation run request")
 
    if not dataset.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Dataset file must be a CSV. Please upload a .csv file."
        )
 
    import tempfile
    import shutil
    from pathlib import Path
 
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            shutil.copyfileobj(dataset.file, tmp)
            tmp_path = Path(tmp.name)
 
        rows = parse_dataset_sample(tmp_path)
 
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        # Always clean up the temp file
        if tmp_path.exists():
            tmp_path.unlink()
 
    if not rows:
        raise HTTPException(
            status_code=422,
            detail="No valid rows found in the dataset CSV. "
                   "Check that your file has the required columns: "
                   "description, question, answer, judge_score, judge_category, NSFW"
        )
 
    try:
        runner = Runner(mode="validation")
        result: RunResult = runner.run(rows)
    except Exception as e:
        #logger.error(f"Validation run failed: {e}")
        raise HTTPException(status_code=500, detail=f"Run failed: {str(e)}")
 
    return _run_result_to_dict(result)
 
 
# ---------------------------------------------------------------------------
# GET /run/{run_id}
# ---------------------------------------------------------------------------
 
# @app.get("/run/{run_id}")
# async def get_run(run_id: str):
    # """
    # Fetch a previously saved run result by run ID.
 
    # Args:
        # run_id : full run UUID or first 8 characters
 
    # Returns:
        # RunResult as JSON, or 404 if not found
    # """
    # logger.info(f"Fetching run: {run_id}")
 
    # result = load_run_result(run_id)
    # if result is None:
        # raise HTTPException(
            # status_code=404,
            # detail=f"No run found with ID '{run_id}'. "
                   # "Check the run ID or use GET /runs to list all saved runs."
        # )
 
    # return _run_result_to_dict(result)
 
 
# ---------------------------------------------------------------------------
# GET /runs
# ---------------------------------------------------------------------------


# @app.get("/runs")
# async def get_all_runs():
    # """
    # List all saved runs in data/raw_runs/.
 
    # Returns:
        # List of run summaries (run_id, mode, total_rows, unsafe_count, timestamp)
        # sorted by most recent first
    # """
    # logger.info("Listing all saved runs")
 
    # summaries = list_saved_runs()
    # return {"runs": summaries, "total": len(summaries)}
 


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
 
@app.get("/health")
async def health():
    """Simple health check. This confirms the server is running."""
    return {"status": "ok", "service": "CharacterGuard API"}