import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .services import extract_text_from_pdf, analyze_contract


def index(request):
    """Home page with upload form."""
    return render(request, 'analyzer/index.html')


def results(request):
    """Results page — renders analysis stored in session."""
    analysis = request.session.get('analysis')
    filename = request.session.get('filename', 'Contract')

    if not analysis:
        return render(request, 'analyzer/index.html', {
            'error': 'No analysis found. Please upload a contract first.'
        })

    # Build context with processed data
    risks = analysis.get('risks', [])
    missing = analysis.get('missing_protections', [])
    positive = analysis.get('positive_clauses', [])
    qs = analysis.get('quick_stats', {})
    level = analysis.get('overall_risk_level', 'Unknown')

    level_colors = {
        'Low': 'low',
        'Medium': 'medium',
        'High': 'high',
        'Critical': 'critical',
    }

    context = {
        'filename': filename,
        'analysis': analysis,
        'risks': risks,
        'missing_protections': missing,
        'positive_clauses': positive,
        'quick_stats': qs,
        'risk_level_class': level_colors.get(level, 'medium'),
        'score': analysis.get('overall_risk_score', 0),
        'level': level,
        'summary': analysis.get('summary', ''),
        'party_info': analysis.get('party_info', {}),
    }
    return render(request, 'analyzer/results.html', context)


@require_http_methods(["POST"])
def analyze_pdf(request):
    """Handle PDF file upload and analyze it."""
    if not settings.ANTHROPIC_API_KEY:
        return JsonResponse({'error': 'API key not configured on server.'}, status=500)

    uploaded_file = request.FILES.get('contract_pdf')
    if not uploaded_file:
        return JsonResponse({'error': 'No file uploaded.'}, status=400)

    if not uploaded_file.name.lower().endswith('.pdf'):
        return JsonResponse({'error': 'Only PDF files are supported.'}, status=400)

    if uploaded_file.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'File size exceeds 10MB limit.'}, status=400)

    try:
        file_bytes = uploaded_file.read()
        contract_text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        return JsonResponse({'error': f'Could not read PDF: {str(e)}'}, status=422)

    if len(contract_text.strip()) < 100:
        return JsonResponse({
            'error': 'PDF appears to be empty or is a scanned image (no extractable text).'
        }, status=422)

    try:
        analysis = analyze_contract(contract_text)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'AI returned an unexpected response. Please try again.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Analysis failed: {str(e)}'}, status=500)

    request.session['analysis'] = analysis
    request.session['filename'] = uploaded_file.name

    return JsonResponse({'success': True, 'redirect': '/results/'})


@require_http_methods(["POST"])
def analyze_text(request):
    """Handle raw contract text and analyze it."""
    if not settings.ANTHROPIC_API_KEY:
        return JsonResponse({'error': 'API key not configured on server.'}, status=500)

    try:
        body = json.loads(request.body)
        contract_text = body.get('text', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request body.'}, status=400)

    if len(contract_text) < 100:
        return JsonResponse({'error': 'Contract text is too short. Please paste more content.'}, status=400)

    try:
        analysis = analyze_contract(contract_text)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'AI returned an unexpected response. Please try again.'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Analysis failed: {str(e)}'}, status=500)

    request.session['analysis'] = analysis
    request.session['filename'] = 'Pasted Contract'

    return JsonResponse({'success': True, 'redirect': '/results/'})
