from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, Any

from .config import settings, BASE_DIR
from .models.schemas import ChatRequest, ChatResponse, AnalysisResponse
from .services.data_loader import data_loader
from .services.router import router
from .services.visualizer import visualizer
from .ml.clustering import spending_clusterer
from .ml.classifier import overspending_detector

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent financial analytics with scikit-learn ML and LangChain RAG architecture."
)

# Enable CORS for React frontend (Localhost & Render deployments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev and hosting
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Detect frontend directory to support unified fullstack deployment on Render
frontend_dir = BASE_DIR.parent / "frontend"
if not frontend_dir.exists():
    frontend_dir = BASE_DIR / "frontend"

if frontend_dir.exists():
    src_dir = frontend_dir / "src"
    if src_dir.exists():
        app.mount("/src", StaticFiles(directory=str(src_dir)), name="frontend_src")

@app.get("/", include_in_schema=False)
def root():
    index_file = frontend_dir / "index.html"
    if frontend_dir.exists() and index_file.exists():
        return FileResponse(str(index_file))
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "endpoints": {
            "chat": "/chat (POST)",
            "analyze": "/analyze (GET)",
            "charts": "/charts (GET)",
            "docs": "/docs (Swagger UI)"
        }
    }

@app.get("/api")
def api_root():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "endpoints": {
            "chat": "/chat (POST)",
            "analyze": "/analyze (GET)",
            "charts": "/charts (GET)",
            "docs": "/docs (Swagger UI)"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Intelligent chat endpoint.
    Automatically routes query between:
    - Personal Transaction Analytics & ML (KMeans & Overspending classifier)
    - Financial Education RAG Pipeline (Vector retrieval over knowledge base)
    """
    try:
        response = router.route_query(request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")

@app.get("/analyze", response_model=AnalysisResponse)
def analyze_endpoint():
    """
    Full ML & Analytics Diagnostic Endpoint:
    - Computes category spending breakdown
    - Fits KMeans to segment spending personas
    - Classifies overspending anomalies
    - Returns actionable summary narrative
    """
    try:
        df = data_loader.load_data()
        stats = data_loader.get_summary_stats()
        
        # ML Clustering
        clustered_df = spending_clusterer.fit_and_cluster(df)
        cluster_summaries = spending_clusterer.get_summaries(clustered_df)
        
        # ML Classification
        alerts = overspending_detector.detect_overspending(df)

        narrative = (
            f"Analyzed {stats['total_transactions']} transactions across {stats['date_range']}. "
            f"Total expenditures stand at ${stats['total_spend']:,.2f} with top outflow in {stats['top_spending_category']}. "
            f"KMeans behavioral clustering identified {len(cluster_summaries)} distinct spending personas. "
            f"Our ML anomaly classifier detected {len(alerts)} irregular spending spikes."
        )

        return AnalysisResponse(
            total_spend=stats["total_spend"],
            total_transactions=stats["total_transactions"],
            date_range=stats["date_range"],
            top_spending_category=stats["top_spending_category"],
            top_spending_amount=stats["top_spending_amount"],
            category_breakdown=stats["category_breakdown"],
            clusters=cluster_summaries,
            overspending_alerts=alerts,
            summary_narrative=narrative
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@app.get("/charts")
def get_charts():
    """
    Generates and returns base64 matplotlib visualizations:
    - Category Spending Breakdown
    - KMeans Spending Behavioral Clusters
    """
    try:
        df = data_loader.load_data()
        clustered_df = spending_clusterer.fit_and_cluster(df)
        
        cat_chart = visualizer.get_category_spending_chart_base64(df)
        cluster_chart = visualizer.get_cluster_scatter_chart_base64(clustered_df)
        
        return {
            "category_chart": cat_chart,
            "cluster_chart": cluster_chart
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart generation error: {str(e)}")
