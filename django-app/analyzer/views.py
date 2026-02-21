import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
import os
import socket

from .services import extract_text_from_pdf, analyze_contract, get_fallback_analysis


def index(request):
    """Home page with upload form."""
    return render(request, "analyzer/index.html")


def results(request):
    """Results page — renders analysis stored in session."""
    analysis = request.session.get("analysis")
    filename = request.session.get("filename", "Contract")

    if not analysis:
        return render(request, "analyzer/index.html", {
            "error": "No analysis found. Please upload a contract first."
        })

    risks = analysis.get("risks", [])
    missing = analysis.get("missing_protections", [])
    positive = analysis.get("positive_clauses", [])
    qs = analysis.get("quick_stats", {})
    level = analysis.get("overall_risk_level", "Unknown")

    level_colors = {
        "Low": "low",
        "Medium": "medium",
        "High": "high",
        "Critical": "critical",
    }

    context = {
        "filename": filename,
        "analysis": analysis,
        "risks": risks,
        "missing_protections": missing,
        "positive_clauses": positive,
        "quick_stats": qs,
        "risk_level_class": level_colors.get(level, "medium"),
        "score": analysis.get("overall_risk_score", 0),
        "level": level,
        "summary": analysis.get("summary", ""),
        "party_info": analysis.get("party_info", {}),
        # Add flag for demo mode
        "is_demo_mode": analysis.get("_is_demo", False),
    }
    return render(request, "analyzer/results.html", context)


def check_ollama_health():
    """Check if Ollama service is reachable"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    
    # Extract base URL for health check
    base_url = ollama_url.replace("/api/chat", "/api/tags")
    
    try:
        # Quick connection test
        response = requests.get(base_url, timeout=3)
        return response.status_code == 200
    except (requests.exceptions.ConnectionError, 
            requests.exceptions.Timeout,
            socket.error):
        return False


@require_http_methods(["POST"])
def analyze_pdf(request):
    """Handle PDF file upload and analyze it."""
    uploaded_file = request.FILES.get("contract_pdf")
    if not uploaded_file:
        return JsonResponse({"error": "No file uploaded."}, status=400)

    if not uploaded_file.name.lower().endswith(".pdf"):
        return JsonResponse({"error": "Only PDF files are supported."}, status=400)

    if uploaded_file.size > 10 * 1024 * 1024:
        return JsonResponse({"error": "File size exceeds 10MB limit."}, status=400)

    try:
        file_bytes = uploaded_file.read()
        contract_text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        return JsonResponse({"error": f"Could not read PDF: {str(e)}"}, status=422)

    if len(contract_text.strip()) < 100:
        return JsonResponse(
            {"error": "PDF appears empty or scanned (no extractable text)."},
            status=422
        )

    # Check Ollama health first
    ollama_available = check_ollama_health()
    
    if not ollama_available:
        # Return a more helpful message for Render deployment
        return JsonResponse({
            "error": "AI service is currently unavailable",
            "details": {
                "message": "The AI analysis service is starting up or unavailable. " +
                          "Please try again in a few minutes.",
                "ollama_url": os.getenv("OLLAMA_URL", "Not configured"),
                "environment": os.getenv("RENDER_SERVICE_NAME", "development"),
                "demo_mode": True
            }
        }, status=503)

    try:
        analysis = analyze_contract(contract_text)
        
        # Store in session
        request.session["analysis"] = analysis
        request.session["filename"] = uploaded_file.name
        
        return JsonResponse({
            "success": True, 
            "redirect": reverse("results")
        })
        
    except requests.exceptions.RequestException as e:
        # Ollama connection error
        return JsonResponse({
            "error": "AI service connection failed",
            "details": {
                "message": str(e),
                "ollama_url": os.getenv("OLLAMA_URL", "Not configured"),
                "suggestion": "If deploying on Render, ensure the Ollama service is running."
            }
        }, status=503)
        
    except ValueError as e:
        # JSON parsing error
        return JsonResponse({
            "error": "AI response parsing failed",
            "details": str(e)
        }, status=500)
        
    except Exception as e:
        # Generic error
        return JsonResponse({
            "error": f"Analysis failed: {str(e)}"
        }, status=500)


@require_http_methods(["POST"])
def analyze_text(request):
    """Handle raw contract text and analyze it."""
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request body."}, status=400)

    contract_text = (body.get("text") or "").strip()
    if len(contract_text) < 100:
        return JsonResponse(
            {"error": "Contract text is too short. Please paste more content."},
            status=400
        )

    # Check Ollama health first
    ollama_available = check_ollama_health()
    
    if not ollama_available:
        return JsonResponse({
            "error": "AI service is currently unavailable",
            "details": {
                "message": "The AI analysis service is starting up or unavailable. " +
                          "Please try again in a few minutes.",
                "demo_mode": True
            }
        }, status=503)

    try:
        analysis = analyze_contract(contract_text)
        
        request.session["analysis"] = analysis
        request.session["filename"] = "Pasted Contract"
        
        return JsonResponse({
            "success": True, 
            "redirect": reverse("results")
        })
        
    except requests.exceptions.RequestException:
        return JsonResponse({
            "error": "AI service is unavailable",
            "details": {
                "message": "Cannot connect to Ollama service.",
                "ollama_url": os.getenv("OLLAMA_URL", "Not configured")
            }
        }, status=503)
        
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=500)
        
    except Exception as e:
        return JsonResponse({"error": f"Analysis failed: {str(e)}"}, status=500)


# Optional: Add a debug endpoint to check service status
@require_http_methods(["GET"])
def service_status(request):
    """Check if Ollama service is reachable (for debugging)"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    ollama_available = check_ollama_health()
    
    return JsonResponse({
        "ollama_available": ollama_available,
        "ollama_url": ollama_url,
        "environment": {
            "render": os.getenv("RENDER", False),
            "service_name": os.getenv("RENDER_SERVICE_NAME", "unknown"),
            "demo_mode": not ollama_available
        }
    })